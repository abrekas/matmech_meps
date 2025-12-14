namespace Matmekh.Maps.Infrastructure
{
    public struct Point : IEquatable<Point>
    {
        public int X { get; }
        public int Y { get; }

        public Point(int x, int y)
        {
            X = x;
            Y = y;
        }

        public override bool Equals(object obj) =>
            obj is Point point && Equals(point);

        public bool Equals(Point other) =>
            X == other.X && Y == other.Y;

        public override int GetHashCode() =>
            HashCode.Combine(X, Y);

        public static bool operator ==(Point left, Point right) =>
            left.Equals(right);

        public static bool operator !=(Point left, Point right) =>
            !(left == right);

        public override string ToString() =>
            $"({X}, {Y})";

        public double DistanceTo(Point other)
        {
            int dx = X - other.X;
            int dy = Y - other.Y;
            return Math.Sqrt(dx * dx + dy * dy);
        }
        public int ManhattanDistance(Point other)
        {
            return Math.Abs(X - other.X) + Math.Abs(Y - other.Y);
        }

        public static Point Parse(string str)
        {
            var parts = str.Split(' ');
            if (parts.Length != 2)
                throw new FormatException($"Неверный формат точки: {str}");

            return new Point(
                int.Parse(parts[0].Trim()),
                int.Parse(parts[1].Trim()));
        }
    }
}
