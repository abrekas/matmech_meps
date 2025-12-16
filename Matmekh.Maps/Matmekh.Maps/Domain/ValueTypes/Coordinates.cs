namespace Matmekh.Maps.Domain.ValueTypes
{
    public struct Coordinates : IEquatable<Coordinates>
    {
        public int X { get; }
        public int Y { get; }
        public string Floor { get; }

        public Coordinates(int x, int y, string floor)
        {
            X = x;
            Y = y;
            Floor = floor;
        }

        public override bool Equals(object obj) =>
            obj is Coordinates point && Equals(point);

        public bool Equals(Coordinates other) =>
            X == other.X && Y == other.Y && Floor == other.Floor;

        public override int GetHashCode() =>
            HashCode.Combine(X, Y);

        public static bool operator ==(Coordinates left, Coordinates right) =>
            left.Equals(right);

        public static bool operator !=(Coordinates left, Coordinates right) =>
            !(left == right);

        public override string ToString() =>
            $"({X}, {Y}, {Floor})";

        public double DistanceTo(Coordinates other)
        {
            int dx = X - other.X;
            int dy = Y - other.Y;
            return Math.Sqrt(dx * dx + dy * dy);
        }
        public int ManhattanDistance(Coordinates other)
        {
            return Math.Abs(X - other.X) + Math.Abs(Y - other.Y);
        }

        public static Coordinates Parse(string str)
        {
            var parts = str.Split(' ');
            if (parts.Length != 3)
                throw new FormatException($"Неверный формат точки: {str}");

            return new Coordinates(
                int.Parse(parts[0].Trim()),
                int.Parse(parts[1].Trim()),
				parts[2].Trim());
        }
    }
}
