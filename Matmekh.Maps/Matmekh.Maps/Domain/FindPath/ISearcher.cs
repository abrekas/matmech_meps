using Matmekh.Maps.Domain.ValueTypes;

namespace Matmekh.Maps.Domain.FindPath
{
    public interface ISearcher
    {
        public List<Coordinates> FindPath(
            Dictionary<Coordinates, List<Coordinates>> graph,
            Coordinates start,
            Coordinates end,
            Func<Coordinates, Coordinates, double>? heuristic = null);
    }
}
