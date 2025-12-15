using Matmekh.Maps.Domain.Entities;

namespace Matmekh.Maps.Domain.ValueTypes
{
    public class CabinetsRoute
    {
        public Cabinet Start { get; private set; }
        public Cabinet End { get; private set; }
        public List<Coordinates> Points { get; private set; }

        public CabinetsRoute(Cabinet start, Cabinet end, List<Coordinates> points)
        {
            Start = start;
            End = end;
            Points = points;
        }

    }
}
