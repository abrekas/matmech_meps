using Matmekh.Maps.Domain;
using Matmekh.Maps.Domain.FindPath;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Matmekh.Maps.Application;

public class PathFinder : IPathFinder
{
    // Приватные поля для кэширования
    private Dictionary<Point, List<Point>>? _graph;
    private Dictionary<string, Point>? _names;
    private readonly object _lock = new object();
    private readonly string BasePath = Path.Combine("Infrastructure");
    private ISearcher searcher;


    public PathFinder(ISearcher search)
    {
        searcher = search;
    }

    // Конвертер JSON для Point
    private class PointJsonConverter : JsonConverter<Point>
    {
        public override Point Read(
            ref Utf8JsonReader reader,
            Type typeToConvert,
            JsonSerializerOptions options)
        {
            var str = reader.GetString();
            return Point.Parse(str!);
        }

        public override void Write(
            Utf8JsonWriter writer,
            Point value,
            JsonSerializerOptions options)
        {
            writer.WriteStringValue($"{value.X},{value.Y}");
        }
    }

    /// <summary>
    /// Загружает граф из graph.json
    /// </summary>
    private Dictionary<Point, List<Point>> LoadGraph()
    {
        var graphPath = Path.Combine(BasePath, "graph.json");

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
        var graph = new Dictionary<Point, List<Point>>();

        foreach (var kvp in stringGraph)
        {
            var point = Point.Parse(kvp.Key);
            var neighbors = kvp.Value.Select(Point.Parse).ToList();
            graph[point] = neighbors;
        }

        Console.WriteLine($"✅ Загружен граф: {graph.Count} точек");
        return graph;
    }

    /// <summary>
    /// Загружает имена из names.json
    /// </summary>
    private Dictionary<string, Point> LoadNames()
    {
        var namesPath = Path.Combine(BasePath, "names.json");

        if (!File.Exists(namesPath))
            throw new FileNotFoundException($"Файл имен не найден: {namesPath}");

        var json = File.ReadAllText(namesPath);
        var options = new JsonSerializerOptions
        {
            Converters = { new PointJsonConverter() }
        };

        var names = JsonSerializer.Deserialize<
            Dictionary<string, Point>>(json, options);

        if (names == null)
            throw new InvalidOperationException("Не удалось десериализовать имена");

        Console.WriteLine($"✅ Загружены имена: {names.Count} названий");
        return names;
    }

    /// <summary>
    /// Возвращает граф (загружает при первом вызове)
    /// </summary>
    public Dictionary<Point, List<Point>> Graph
    {
        get
        {
            if (_graph == null)
            {
                lock (_lock)
                {
                    _graph ??= LoadGraph();
                }
            }
            return _graph;
        }
    }

    /// <summary>
    /// Возвращает словарь имен (загружает при первом вызове)
    /// </summary>
    public Dictionary<string, Point> Names
    {
        get
        {
            if (_names == null)
            {
                lock (_lock)
                {
                    _names ??= LoadNames();
                }
            }
            return _names;
        }
    }

    /// <summary>
    /// Обновляет граф из файла (если файл изменился)
    /// </summary>
    public void ReloadGraph()
    {
        lock (_lock)
        {
            _graph = LoadGraph();
        }
    }

    /// <summary>
    /// Обновляет имена из файла (если файл изменился)
    /// </summary>
    public void ReloadNames()
    {
        lock (_lock)
        {
            _names = LoadNames();
        }
    }

    /// <summary>
    /// Основной метод поиска пути
    /// </summary>
    /// <param name="startName">Название начальной точки</param>
    /// <param name="endName">Название конечной точки</param>
    /// <returns>Список точек пути или пустой список если путь не найден</returns>
    public List<Point> FindPath(string startName, string endName)
    {
        // 1. Проверяем существование имен
        if (!Names.TryGetValue(startName, out var startPoint))
            throw new ArgumentException($"Не найдена начальная точка: {startName}");

        if (!Names.TryGetValue(endName, out var endPoint))
            throw new ArgumentException($"Не найдена конечная точка: {endName}");

        Console.WriteLine($"📍 Поиск пути: {startName} {startPoint} → {endName} {endPoint}");

        // 2. Проверяем существование точек в графе
        if (!Graph.ContainsKey(startPoint))
            throw new InvalidOperationException($"Точка {startPoint} не найдена в графе");

        if (!Graph.ContainsKey(endPoint))
            throw new InvalidOperationException($"Точка {endPoint} не найдена в графе");

        // 3. Вызываем алгоритм A*
        var path = searcher.FindPath(Graph, startPoint, endPoint);

        // 4. Логируем результат
        if (path.Count > 0)
        {
            Console.WriteLine($"✅ Найден путь длиной {path.Count} шагов:");
            Console.WriteLine($"   {string.Join(" → ", path.Select(p => p.ToString()))}");

            // Конвертируем в названия если возможно
            var namedPath = path.Select(p =>
                Names.FirstOrDefault(n => n.Value.Equals(p)).Key ?? p.ToString());
            Console.WriteLine($"   По названиям: {string.Join(" → ", namedPath)}");
        }
        else
        {
            Console.WriteLine("❌ Путь не найден");
        }

        return path;
    }

    /// <summary>
    /// Находит путь и возвращает названия точек
    /// </summary>
    public List<string> FindPathAsNames(string startName, string endName)
    {
        var path = FindPath(startName, endName);

        // Конвертируем точки в названия
        var result = new List<string>();
        foreach (var point in path)
        {
            var name = Names.FirstOrDefault(n => n.Value.Equals(point)).Key;
            result.Add(name ?? point.ToString());
        }

        return result;
    }

    /// <summary>
    /// Находит путь и возвращает смешанный список (точки + названия)
    /// </summary>
    public List<object> FindPathMixed(string startName, string endName)
    {
        var path = FindPath(startName, endName);
        var result = new List<object>();

        foreach (var point in path)
        {
            var name = Names.FirstOrDefault(n => n.Value.Equals(point)).Key;
            if (name != null)
                result.Add(new { Name = name, Point = point });
            else
                result.Add(point);
        }

        return result;
    }

    /// <summary>
    /// Получает все доступные названия точек
    /// </summary>
    public List<string> GetAllLocationNames()
    {
        return Names.Keys.OrderBy(x => x).ToList();
    }

    /// <summary>
    /// Получает соседей точки по названию
    /// </summary>
    public List<string> GetNeighbors(string locationName)
    {
        if (!Names.TryGetValue(locationName, out var point))
            throw new ArgumentException($"Не найдена точка: {locationName}");

        if (!Graph.TryGetValue(point, out var neighborPoints))
            return new List<string>();

        // Конвертируем соседей в названия
        var neighbors = new List<string>();
        foreach (var neighborPoint in neighborPoints)
        {
            var name = Names.FirstOrDefault(n => n.Value.Equals(neighborPoint)).Key;
            neighbors.Add(name ?? neighborPoint.ToString());
        }

        return neighbors;
    }

    /// <summary>
    /// Проверяет существование точки по названию
    /// </summary>
    public bool LocationExists(string locationName)
    {
        return Names.ContainsKey(locationName);
    }

    /// <summary>
    /// Получает координаты точки по названию
    /// </summary>
    public Point? GetPointByName(string locationName)
    {
        return Names.TryGetValue(locationName, out var point) ? point : null;
    }

    /// <summary>
    /// Получает название по координатам
    /// </summary>
    public string? GetNameByPoint(Point point)
    {
        return Names.FirstOrDefault(n => n.Value.Equals(point)).Key;
    }
}