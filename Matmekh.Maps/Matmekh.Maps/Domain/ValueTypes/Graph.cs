using Matmekh.Maps.Domain.Entities;
using Matmekh.Maps.Infrastructure.Scripts;

namespace Matmekh.Maps.Domain.ValueTypes
{
	public class Graph : IGraph
	{
		private Dictionary<Coordinates, List<Coordinates>>? _graph;
		private Dictionary<string, Cabinet>? _names;

		private readonly object _lock = new object();
		/// <summary>
		/// Возвращает граф (загружает при первом вызове)
		/// </summary>
		public Dictionary<Coordinates, List<Coordinates>> GraphDictionary
		{
			get
			{
				if (_graph == null)
				{
					lock (_lock)
					{
						_graph ??= graphLoader.LoadGraph();
					}
				}
				return _graph;
			}
		}

		/// <summary>
		/// Возвращает словарь имен (загружает при первом вызове)
		/// </summary>
		public Dictionary<string, Cabinet> Names
		{
			get
			{
				if (_names == null)
				{
					lock (_lock)
					{
						_names ??= graphLoader.LoadNames();
					}
				}
				return _names;
			}
		}

		private IJSONGraphLoader graphLoader;

		public Graph(IJSONGraphLoader graphLoader)
		{
			this.graphLoader = graphLoader;
		}
	}
}
