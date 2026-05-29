package com.zoo;

class Animal {
    String describe() {
        return "animal";
    }
}

class Lion extends Animal {
    String describe() {
        return "lion";
    }

    void roar() {
    }
}

class Zoo {
    Animal create() {
        return new Lion();
    }
}
