#include <QAudioOutput>
#include <QGuiApplication>
#include <QElapsedTimer>
#include <QMediaPlayer>
#include <QTimer>
#include <QUrl>
#include <QVideoFrame>
#include <QVideoSink>

#include <deque>
#include <iostream>

int main(int argc, char** argv) {
    QGuiApplication application(argc, argv);
    const auto arguments = application.arguments();
    if (arguments.size() < 3) {
        std::cerr << "usage: qt_seek_probe VIDEO SEEK_MS [SEEK_MS ...]\n";
        return 2;
    }

    std::deque<qint64> targets;
    for (qsizetype i = 2; i < arguments.size(); ++i) {
        bool valid = false;
        const auto target = arguments[i].toLongLong(&valid);
        if (!valid || target < 0) {
            std::cerr << "invalid seek position\n";
            return 2;
        }
        targets.push_back(target);
    }

    QAudioOutput audio;
    audio.setMuted(true);
    QVideoSink sink;
    QMediaPlayer player;
    player.setAudioOutput(&audio);
    player.setVideoSink(&sink);
    QTimer timeout;
    timeout.setSingleShot(true);
    QElapsedTimer elapsed;
    bool pending = false;

    const auto seek_next = [&] {
        if (targets.empty()) {
            application.quit();
            return;
        }
        elapsed.start();
        pending = true;
        timeout.start(5000);
        player.setPosition(targets.front());
    };
    QObject::connect(&timeout, &QTimer::timeout, &application, [&] {
        if (pending)
            std::cout << targets.front() << ",missing,\n";
        application.exit(1);
    });
    QObject::connect(&player, &QMediaPlayer::errorOccurred, &application,
                     [&](QMediaPlayer::Error error) {
        std::cerr << "Qt Multimedia error " << int(error) << '\n';
        application.exit(1);
    });
    QObject::connect(&sink, &QVideoSink::videoFrameChanged, &application,
                     [&](const QVideoFrame& frame) {
        if (!frame.isValid() || frame.startTime() < 0)
            return;
        if (!elapsed.isValid()) {
            QTimer::singleShot(0, &application, seek_next);
            elapsed.start();
            return;
        }
        if (!pending)
            return;
        const auto pts_ms = frame.startTime() / 1000;
        // Qt exposes timestamps but no seek generation. This is a candidate
        // frame in a serial diagnostic, not proof of request attribution.
        if (pts_ms < targets.front() || pts_ms - targets.front() > 100)
            return;
        std::cout << targets.front() << ",ok," << elapsed.nsecsElapsed() / 1'000'000.0 << '\n';
        pending = false;
        targets.pop_front();
        timeout.stop();
        QTimer::singleShot(0, &application, seek_next);
    });

    std::cout << "target_ms,result,seek_to_sink_candidate_ms\n";
    QTimer::singleShot(0, &application, [&] {
        timeout.start(15000);
        player.setSource(QUrl::fromLocalFile(arguments[1]));
        player.play();
    });
    return application.exec();
}
