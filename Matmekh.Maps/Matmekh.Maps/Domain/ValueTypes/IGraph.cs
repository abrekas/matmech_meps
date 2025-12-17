using Matmekh.Maps.Domain.Entities;

namespace Matmekh.Maps.Domain.ValueTypes
{
	public interface IGraph
	{
		public Dictionary<string, Cabinet> Names { get; }
		public Dictionary<Coordinates, List<Coordinates>> GraphDictionary { get; }
	}
}
