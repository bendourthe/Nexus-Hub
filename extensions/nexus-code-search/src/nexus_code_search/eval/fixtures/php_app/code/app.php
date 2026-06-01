<?php

namespace App;

const MAX = 10;

class Greeter
{
    private $name;

    public function __construct($name)
    {
        $this->name = $name;
    }

    public function announce()
    {
        return greet($this->name);
    }
}

function greet($n)
{
    return $n;
}
