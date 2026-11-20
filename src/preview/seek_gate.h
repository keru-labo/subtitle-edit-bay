#pragma once

#include <cstdint>
#include <optional>

namespace preview {

enum class Media { original, proxy };

struct Seek {
    std::uint64_t generation;
    std::int64_t timeline_us;
    Media media;
};

// One owner thread orders requests, dispatch and publication. Workers return
// their original generation with decoded video and audio.
class SeekGate {
public:
    void request(std::int64_t timeline_us, Media media) {
        pending_ = Seek{++generation_, timeline_us, media};
    }

    std::optional<Seek> take_latest() {
        auto request = pending_;
        if (request)
            dispatched_ = request->generation;
        pending_.reset();
        return request;
    }

    void invalidate() {
        ++generation_;
        pending_.reset();
    }

    bool may_publish(std::uint64_t generation) const {
        return generation != 0 && generation == generation_ && generation == dispatched_;
    }

private:
    std::uint64_t generation_ = 0;
    std::uint64_t dispatched_ = 0;
    std::optional<Seek> pending_;
};

} // namespace preview
