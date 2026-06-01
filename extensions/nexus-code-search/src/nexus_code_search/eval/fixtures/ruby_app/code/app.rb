require 'set'

module Animals
  class Base
  end

  class Greeter < Base
    def initialize(name)
      @name = name
    end

    def greet
      hello(@name)
    end
  end
end

def hello(text)
  text
end
