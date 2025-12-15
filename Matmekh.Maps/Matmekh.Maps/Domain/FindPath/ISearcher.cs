namespace Matmekh.Maps.Domain.FindPath
{
    public interface ISearcher
    {
		public List<Point> FindPath(
			Dictionary<Point, List<Point>> graph,
			Point start,
			Point end,
			Func<Point, Point, double>? heuristic = null);
	}
}
