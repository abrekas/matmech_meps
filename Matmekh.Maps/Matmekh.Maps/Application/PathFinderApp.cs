using Matmekh.Maps.Domain.FindPath;
using Matmekh.Maps.Domain.ValueTypes;
using Matmekh.Maps.Infrastructure.Scripts;

namespace Matmekh.Maps.Application
{
	public class PathFinderApp : IPathFinderApp
	{
		private IPathFinderService _pathFinderService;

		public PathFinderApp(IPathFinderService pathFinderService)
		{
			_pathFinderService = pathFinderService;
		}

		public CabinetsRoute FindPath(string startName, string endName)
		{
			return _pathFinderService.FindPath(startName, endName);
		}
	}
}
