#pragma once

#include "seek_gate.h"
#include <functional>
#include <string>

namespace preview {

// The adapter serializes these callbacks onto the UI owner thread.
struct PlaybackEvents {
    std::function<void(std::uint64_t, std::int64_t)> position_changed;
    std::function<void(std::uint64_t, const std::string&)> error;
};

class PlaybackBackend {
public:
    virtual ~PlaybackBackend() = default;
    virtual void set_events(PlaybackEvents events) = 0;
    virtual void play() = 0;
    virtual void pause() = 0;
    virtual void stop() = 0;
    virtual void seek(Seek request) = 0;
    virtual void set_volume(double linear_gain) = 0;
    virtual void set_muted(bool muted) = 0;
};

} // namespace preview
