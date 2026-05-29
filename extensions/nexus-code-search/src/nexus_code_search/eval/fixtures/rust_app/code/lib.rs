use std::fmt;

trait Shape {
    fn area(&self) -> f64;
}

struct Circle {
    radius: f64,
}

impl Shape for Circle {
    fn area(&self) -> f64 {
        self.radius
    }
}

impl Circle {
    fn make(r: f64) -> Circle {
        Circle { radius: r }
    }
}

fn run() {
    let c = Circle::make(1.0);
    c.area();
}
