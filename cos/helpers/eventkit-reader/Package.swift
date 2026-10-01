// swift-tools-version:5.10
// eventkit-reader: read-only Calendar/Reminders JSON for the Chief of Staff (M1).
import PackageDescription

let package = Package(
    name: "eventkit-reader",
    platforms: [.macOS(.v14)],
    targets: [
        .executableTarget(
            name: "eventkit-reader",
            path: "Sources/eventkit-reader",
            exclude: ["Info.plist"],
            linkerSettings: [
                // Embed Info.plist so macOS can show the usage descriptions on first access.
                .unsafeFlags([
                    "-Xlinker", "-sectcreate", "-Xlinker", "__TEXT",
                    "-Xlinker", "__info_plist",
                    "-Xlinker", "Sources/eventkit-reader/Info.plist",
                ]),
            ]
        ),
    ]
)
