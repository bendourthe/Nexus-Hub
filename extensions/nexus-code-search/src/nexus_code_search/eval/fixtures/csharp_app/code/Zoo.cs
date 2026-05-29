namespace Zoo;

class Animal
{
    public virtual string Describe()
    {
        return "animal";
    }
}

class Lion : Animal
{
    public override string Describe()
    {
        return "lion";
    }

    public void Roar()
    {
    }
}

class ZooKeeper
{
    public Animal Create()
    {
        return new Lion();
    }
}
