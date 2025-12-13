namespace Matmekh.Maps.Infrastructure
{
    public class Node : IComparable<Node>
    {
        public Point Position { get; }
        public Node? Parent { get; set; }
        public double G { get; set; }
        public double H { get; set; }
        public double F => G + H;

        public Node(Point position)
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
