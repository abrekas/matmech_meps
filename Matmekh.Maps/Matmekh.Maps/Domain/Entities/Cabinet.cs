using Matmekh.Maps.Domain.ValueTypes;

namespace Matmekh.Maps.Domain.Entities
{
    public class Cabinet
    {
        public string Name { get; private set; }
        public Coordinates Location { get; private set; }

        public Cabinet(string name, Coordinates location)
        {
            Name = name;
            Location = location;
        }
    }
}
