using Matmekh.Maps.Domain.Entities;
using Matmekh.Maps.Domain.ValueTypes;
using System.Text.Json;

namespace Matmekh.Maps.Infrastructure.Scripts
{
    public class JSONGraphLoader : IJSONGraphLoader
	{
		/// <summary>
		/// Загружает граф из graph.json
		/// </summary>
		public Dictionary<Coordinates, List<Coordinates>> LoadGraph()
		{
			var graphPath = Path.Combine("Infrastructure", "graph.json");

			if (!File.Exists(graphPath))
				throw new FileNotFoundException($"Файл графа не найден: {graphPath}");

			var json = File.ReadAllText(graphPath);

			var options = new JsonSerializerOptions
			{
				Converters = { new PointJsonConverter() }
			};

			// Десериализуем как Dictionary<string, List<string>>
			var stringGraph = JsonSerializer.Deserialize<
				Dictionary<string, List<string>>>(json, options);

			if (stringGraph == null)
				throw new InvalidOperationException("Не удалось десериализовать граф");

			// Конвертируем в Dictionary<Point, List<Point>>
			var graph = new Dictionary<Coordinates, List<Coordinates>>();

			foreach (var kvp in stringGraph)
			{
				var point = Coordinates.Parse(kvp.Key);
				var neighbors = kvp.Value.Select(Coordinates.Parse).ToList();
				graph[point] = neighbors;
			}

			Console.WriteLine($"Загружен граф: {graph.Count} точек");
			return graph;
		}

		/// <summary>
		/// Загружает имена из names.json
		/// </summary>
		public Dictionary<string, Cabinet> LoadNames()
		{
			var namesPath = Path.Combine("Infrastructure", "names.json");

			if (!File.Exists(namesPath))
				throw new FileNotFoundException($"Файл имен не найден: {namesPath}");

			var json = File.ReadAllText(namesPath);
			var options = new JsonSerializerOptions
			{
				Converters = { new PointJsonConverter() }
			};

			var names = JsonSerializer.Deserialize<
				Dictionary<string, Coordinates>>(json, options);
			var namesCabinets = names.Select(p => new KeyValuePair<string, Cabinet>(p.Key, new Cabinet(p.Key, p.Value))).ToDictionary();

			if (names == null)
				throw new InvalidOperationException("Не удалось десериализовать имена");

			Console.WriteLine($"✅ Загружены имена: {names.Count} названий");
			return namesCabinets;
		}
	}
}
