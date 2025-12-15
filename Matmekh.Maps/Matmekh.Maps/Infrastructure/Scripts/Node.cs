using Matmekh.Maps.Domain.ValueTypes;

namespace Matmekh.Maps.Infrastructure.Scripts
{
    public class Node : IComparable<Node>
    {
        public Coordinates Position { get; }
        public Node? Parent { get; set; }
        public double G { get; set; }
        public double H { get; set; }
        public double F => G + H;

        public Node(Coordinates position)
        {
            Position = position;
            G = 0;
            H = 0;
        }

        public int CompareTo(Node? other)
        {
            if (other == null) return 1;
            return F.CompareTo(other.F);
        }
    }
}
