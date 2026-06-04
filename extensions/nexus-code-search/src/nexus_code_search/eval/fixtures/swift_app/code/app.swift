import Foundation

protocol Greeter {
    func describe() -> String
}

class Base {
}

class Animal: Base {
    let name: String

    init(name: String) {
        self.name = name
    }

    func greet() -> String {
        return hello(name)
    }
}

struct Point {
    var x: Int
}

enum Color {
    case red
}

func hello(_ text: String) -> String {
    return text
}
