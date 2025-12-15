using Matmekh.Maps.Domain.Entities;
using Matmekh.Maps.Domain.ValueTypes;

namespace Matmekh.Maps.Infrastructure.Scripts
{
    public interface IJSONGraphLoader
    {
		public Dictionary<Coordinates, List<Coordinates>> LoadGraph();
		public Dictionary<string, Cabinet> LoadNames();

	}
}
