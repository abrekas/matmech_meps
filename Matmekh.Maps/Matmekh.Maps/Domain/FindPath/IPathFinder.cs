namespace Matmekh.Maps.Domain.FindPath
{
	public interface IPathFinder
	{
		public List<Point> FindPath(string startName, string endName);
	}
}
