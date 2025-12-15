using Matmekh.Maps.Domain.ValueTypes;
using Matmekh.Maps.Infrastructure.Scripts;

namespace Matmekh.Maps.Domain.FindPath
{
    public interface IPathFinderService
	{
		public CabinetsRoute FindPath(string startName, string endName);
	}
}
