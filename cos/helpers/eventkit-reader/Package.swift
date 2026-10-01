// swift-tools-version:5.10
// eventkit-reader: read-only Calendar/Reminders JSON for the Chief of Staff (M1).
// Packaged as ChiefOfStaffEventKitReader.app by scripts/cos-build-eventkit-helper.sh,
// which supplies the bundle Info.plist (App/Info.plist) and signs the bundle.
import PackageDescription

let package = Package(
    name: "eventkit-reader",
    platforms: [.macOS(.v14)],
    targets: [
        .executableTarget(name: "eventkit-reader", path: "Sources/eventkit-reader"),
    ]
)
