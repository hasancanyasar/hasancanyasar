// Poppins metnini macOS CoreText ile fonttan bağımsız SVG yollarına çevirir.
import Foundation
import CoreText
import CoreGraphics

let args = CommandLine.arguments
let url = URL(fileURLWithPath: args[1])
let data = try Data(contentsOf: url)
let provider = CGDataProvider(data: data as CFData)!
let font = CTFontCreateWithGraphicsFont(CGFont(provider)!, Double(args[2])!, nil, nil)
let line = CTLineCreateWithAttributedString(NSAttributedString(string: args[3], attributes: [NSAttributedString.Key(kCTFontAttributeName as String): font]))
var fragments: [String] = []
func point(_ p: CGPoint) -> String { String(format: "%.2f %.2f", p.x, p.y) }
for item in CTLineGetGlyphRuns(line) as! [CTRun] {
    let count = CTRunGetGlyphCount(item)
    var glyphs = [CGGlyph](repeating: 0, count: count)
    var positions = [CGPoint](repeating: .zero, count: count)
    CTRunGetGlyphs(item, CFRange(location: 0, length: count), &glyphs)
    CTRunGetPositions(item, CFRange(location: 0, length: count), &positions)
    for i in 0..<count {
        var transform = CGAffineTransform(translationX: positions[i].x, y: positions[i].y)
        guard let path = CTFontCreatePathForGlyph(font, glyphs[i], &transform) else { continue }
        path.applyWithBlock { pointer in
            let e = pointer.pointee
            switch e.type {
            case .moveToPoint: fragments.append("M" + point(e.points[0]))
            case .addLineToPoint: fragments.append("L" + point(e.points[0]))
            case .addQuadCurveToPoint: fragments.append("Q" + point(e.points[0]) + " " + point(e.points[1]))
            case .addCurveToPoint: fragments.append("C" + point(e.points[0]) + " " + point(e.points[1]) + " " + point(e.points[2]))
            case .closeSubpath: fragments.append("Z")
            @unknown default: break
            }
        }
    }
}
let result: [String: Any] = ["path": fragments.joined(), "width": CTLineGetTypographicBounds(line, nil, nil, nil)]
print(String(data: try JSONSerialization.data(withJSONObject: result, options: [.sortedKeys]), encoding: .utf8)!)
