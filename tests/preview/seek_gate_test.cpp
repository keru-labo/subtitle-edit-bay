#include "playback_backend.h"

#ifdef NDEBUG
#undef NDEBUG
#endif
#include <cassert>

using preview::Media;
using preview::SeekGate;

int main() {
    SeekGate gate;

    // Given a newly opened session, no worker has a publishable generation.
    assert(!gate.may_publish(0));
    assert(!gate.take_latest());

    // When the user scrubs twice before dispatch, only the latest target leaves.
    gate.request(250'000, Media::proxy);
    gate.request(750'000, Media::proxy);
    assert(!gate.may_publish(2));
    const auto proxy = gate.take_latest();
    assert(proxy && proxy->generation == 2 && proxy->media == Media::proxy);
    assert(proxy->timeline_us == 750'000);
    assert(!gate.take_latest());
    assert(gate.may_publish(proxy->generation));

    // When scrubbing ends, the original uses the same timeline coordinate.
    gate.request(proxy->timeline_us, Media::original);
    assert(!gate.may_publish(proxy->generation));
    const auto original = gate.take_latest();
    assert(original && original->timeline_us == proxy->timeline_us);
    assert(original->media == Media::original);
    assert(!gate.may_publish(proxy->generation));
    assert(gate.may_publish(original->generation));

    // When playback stops or the source changes, late and queued work is dropped.
    gate.request(900'000, Media::proxy);
    gate.invalidate();
    assert(!gate.take_latest());
    assert(!gate.may_publish(original->generation));
    assert(!gate.may_publish(original->generation + 2));
}
