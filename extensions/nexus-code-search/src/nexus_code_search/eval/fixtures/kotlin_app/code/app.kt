package com.example

import kotlin.collections.List

interface Greeter {
    fun describe(): String
}

open class Base

class Animal(val name: String) : Base(), Greeter {
    override fun describe(): String {
        return name
    }

    fun greet(): String {
        return hello(name)
    }
}

object Singleton {
    fun ping(): Int {
        return 1
    }
}

enum class Color {
    RED,
    GREEN
}

fun hello(text: String): String {
    return text
}
