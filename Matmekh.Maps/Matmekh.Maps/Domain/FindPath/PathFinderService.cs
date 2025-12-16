using Matmekh.Maps.Infrastructure.Scripts;
using Matmekh.Maps.Domain.Entities;
using Matmekh.Maps.Domain.ValueTypes;

namespace Matmekh.Maps.Domain.FindPath;

public class PathFinderService : IPathFinderService
{
    private ISearcher searcher;
    private IGraph graph;

	public Dictionary<Coordinates, List<Coordinates>> Graph 
    { 
        get 
        { 
            return graph.GraphDictionary;
        } 
    }

	public Dictionary<string, Cabinet> Names
	{
		get
		{
			return graph.Names;
		}
	}


	public PathFinderService(ISearcher search, IGraph graph)
    {
        searcher = search;
        this.graph = graph;

	}

    /// <summary>
    /// Основной метод поиска пути
    /// </summary>
    /// <param name="startName">Название начальной точки</param>
    /// <param name="endName">Название конечной точки</param>
    /// <returns>Список точек пути или пустой список если путь не найден</returns>
    public CabinetsRoute FindPath(string startName, string endName)
    {

        // 1. Проверяем существование имен
        if (!Names.TryGetValue(startName, out var startPoint))
            throw new ArgumentException($"Не найдена начальная точка: {startName}");

        if (!Names.TryGetValue(endName, out var endPoint))
            throw new ArgumentException($"Не найдена конечная точка: {endName}");

        Console.WriteLine($"Поиск пути: {startName} {startPoint} → {endName} {endPoint}");

        // 2. Проверяем существование точек в графе
        if (!Graph.ContainsKey(startPoint.Location))
            throw new InvalidOperationException($"Точка {startPoint} не найдена в графе");

        if (!Graph.ContainsKey(endPoint.Location))
            throw new InvalidOperationException($"Точка {endPoint} не найдена в графе");

        // 3. Вызываем алгоритм A*
        var path = searcher.FindPath(Graph, startPoint.Location, endPoint.Location);

        // 4. Логируем результат
        if (path.Count > 0)
        {
            Console.WriteLine($"Найден путь длиной {path.Count} шагов:");
            Console.WriteLine($"   {string.Join(" → ", path.Select(p => p.ToString()))}");

            // Конвертируем в названия если возможно
            var namedPath = path.Select(p =>
                Names.FirstOrDefault(n => n.Value.Equals(p)).Key ?? p.ToString());
            Console.WriteLine($"   По названиям: {string.Join(" → ", namedPath)}");
        }
        else
        {
            Console.WriteLine("Путь не найден");
        }

        var result = new CabinetsRoute(startPoint, endPoint, path);

        return result;
    }
}