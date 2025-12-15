using Matmekh.Maps.Domain.ValueTypes;

namespace Matmekh.Maps.Application
{
	public interface IPathFinderApp
	{
		public CabinetsRoute FindPath(string startName, string endName);
	}
}
