#include <d3d11.h>

extern "C" {
#include <libavcodec/avcodec.h>
#include <libavformat/avformat.h>
#include <libavutil/hwcontext.h>
#include <libavutil/hwcontext_d3d11va.h>
}

#include <chrono>
#include <cstdint>
#include <string>
#include <iostream>
#include <memory>
#include <stdexcept>

using Clock = std::chrono::steady_clock;

namespace {

void check(int result, const char* operation) {
    if (result < 0)
        throw std::runtime_error(operation);
}

AVPixelFormat d3d11_format(AVCodecContext*, const AVPixelFormat* formats) {
    for (; *formats != AV_PIX_FMT_NONE; ++formats)
        if (*formats == AV_PIX_FMT_D3D11)
            return *formats;
    return AV_PIX_FMT_NONE;
}

template <typename T, void (*Free)(T**)>
struct FreeAv {
    void operator()(T* value) const { Free(&value); }
};

void submit_gpu_copy(const AVFrame& frame, const AVD3D11VADeviceContext& d3d) {
    if (frame.format != AV_PIX_FMT_D3D11 || !frame.data[0])
        throw std::runtime_error("expected a D3D11 texture");
    auto* texture = reinterpret_cast<ID3D11Texture2D*>(frame.data[0]);
    ID3D11Device* texture_device = nullptr;
    texture->GetDevice(&texture_device);
    const bool same_device = texture_device == d3d.device;
    texture_device->Release();
    if (!same_device)
        throw std::runtime_error("decoder texture belongs to another device");

    D3D11_TEXTURE2D_DESC desc{};
    texture->GetDesc(&desc);
    if (desc.CPUAccessFlags != 0 || desc.Usage == D3D11_USAGE_STAGING)
        throw std::runtime_error("unexpected CPU-accessible texture");

    const auto slice = reinterpret_cast<std::uintptr_t>(frame.data[1]);
    if (slice >= desc.ArraySize || desc.MipLevels != 1)
        throw std::runtime_error("unexpected decoder subresource");
    desc.ArraySize = 1;
    desc.Usage = D3D11_USAGE_DEFAULT;
    desc.BindFlags = D3D11_BIND_SHADER_RESOURCE;
    desc.MiscFlags = 0;
    ID3D11Texture2D* destination = nullptr;
    if (FAILED(d3d.device->CreateTexture2D(&desc, nullptr, &destination)))
        throw std::runtime_error("create GPU shader-resource texture");

    d3d.lock(d3d.lock_ctx);
    d3d.device_context->CopySubresourceRegion(destination, 0, 0, 0, 0,
                                               texture, static_cast<UINT>(slice), nullptr);
    d3d.unlock(d3d.lock_ctx);
    destination->Release();
}

bool drain(AVCodecContext* codec, AVFrame* frame, const AVD3D11VADeviceContext& d3d,
           std::int64_t target) {
    int status;
    while ((status = avcodec_receive_frame(codec, frame)) >= 0) {
        const auto pts = frame->best_effort_timestamp;
        const bool found = pts != AV_NOPTS_VALUE && pts >= target;
        if (found)
            submit_gpu_copy(*frame, d3d);
        av_frame_unref(frame);
        if (found)
            return true;
    }
    if (status != AVERROR(EAGAIN) && status != AVERROR_EOF)
        check(status, "receive frame");
    return false;
}

bool decode_to(AVFormatContext* input, AVCodecContext* codec, AVPacket* packet,
               AVFrame* frame, int stream, const AVD3D11VADeviceContext& d3d, std::int64_t target) {
    int status;
    while ((status = av_read_frame(input, packet)) >= 0) {
        const bool video = packet->stream_index == stream;
        if (video)
            check(avcodec_send_packet(codec, packet), "send packet");
        av_packet_unref(packet);
        if (video && drain(codec, frame, d3d, target))
            return true;
    }
    if (status != AVERROR_EOF)
        check(status, "read packet");
    check(avcodec_send_packet(codec, nullptr), "flush pending frames");
    return drain(codec, frame, d3d, target);
}

} // namespace

int main(int argc, char** argv) {
    if (argc < 3) {
        std::cerr << "usage: d3d11_decode_probe VIDEO SEEK_MS [SEEK_MS ...]\n";
        return 2;
    }
    try {
        AVFormatContext* raw_input = nullptr;
        check(avformat_open_input(&raw_input, argv[1], nullptr, nullptr), "open input");
        std::unique_ptr<AVFormatContext, FreeAv<AVFormatContext, avformat_close_input>> input(raw_input);
        check(avformat_find_stream_info(input.get(), nullptr), "find stream info");

        const AVCodec* decoder = nullptr;
        const int index = av_find_best_stream(input.get(), AVMEDIA_TYPE_VIDEO, -1, -1, &decoder, 0);
        check(index, "find video stream");
        const auto* stream = input->streams[index];
        std::unique_ptr<AVCodecContext, FreeAv<AVCodecContext, avcodec_free_context>> codec(
            avcodec_alloc_context3(decoder));
        std::unique_ptr<AVPacket, FreeAv<AVPacket, av_packet_free>> packet(av_packet_alloc());
        std::unique_ptr<AVFrame, FreeAv<AVFrame, av_frame_free>> frame(av_frame_alloc());
        if (!codec || !packet || !frame)
            throw std::runtime_error("allocate FFmpeg context");
        check(avcodec_parameters_to_context(codec.get(), stream->codecpar), "configure decoder");
        check(av_hwdevice_ctx_create(&codec->hw_device_ctx, AV_HWDEVICE_TYPE_D3D11VA,
                                     nullptr, nullptr, 0), "create D3D11VA device");
        const auto* hw = reinterpret_cast<AVHWDeviceContext*>(codec->hw_device_ctx->data);
        const auto* d3d = static_cast<AVD3D11VADeviceContext*>(hw->hwctx);
        codec->get_format = d3d11_format;
        check(avcodec_open2(codec.get(), decoder, nullptr), "open decoder");

        const auto origin = stream->start_time == AV_NOPTS_VALUE ? 0 : stream->start_time;
        std::cout << "target_ms,result,seek_to_gpu_copy_submission_ms\n";
        for (int i = 2; i < argc; ++i) {
            std::size_t parsed = 0;
            const auto milliseconds = std::stoll(argv[i], &parsed);
            if (argv[i][parsed] != '\0' || milliseconds < 0)
                throw std::runtime_error("invalid seek position");
            const auto target = origin + av_rescale_q(milliseconds, {1, 1000}, stream->time_base);
            const auto start = Clock::now();
            check(av_seek_frame(input.get(), index, target, AVSEEK_FLAG_BACKWARD), "seek");
            avcodec_flush_buffers(codec.get());
            const bool found = decode_to(input.get(), codec.get(), packet.get(), frame.get(),
                                         index, *d3d, target);
            const auto elapsed = std::chrono::duration<double, std::milli>(Clock::now() - start).count();
            std::cout << milliseconds << (found ? ",ok," : ",missing,");
            if (found)
                std::cout << elapsed;
            std::cout << '\n';
        }
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
