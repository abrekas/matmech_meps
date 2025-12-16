using Matmekh.Maps.Domain.ValueTypes;
using Matmekh.Maps.Infrastructure.Scripts;

namespace Matmekh.Maps.Domain.FindPath
{
    public class AStar : ISearcher
    {
        /// <summary>
        /// Находит путь от start до end в графе
        /// </summary>
        /// <param name="graph">Словарь: точка -> список соседних точек</param>
        /// <param name="start">Начальная точка</param>
        /// <param name="end">Конечная точка</param>
        /// <param name="heuristic">Функция эвристики (null = Манхэттенское расстояние)</param>
        /// <returns>Список точек от start до end или пустой список если путь не найден</returns>
        public List<Coordinates> FindPath(
            Dictionary<Coordinates, List<Coordinates>> graph,
            Coordinates start,
            Coordinates end,
            Func<Coordinates, Coordinates, double>? heuristic = null)
        {
            // Проверка входных данных
            if (!graph.ContainsKey(start))
                throw new ArgumentException($"Начальная точка {start} не найдена в графе");

            if (!graph.ContainsKey(end))
                throw new ArgumentException($"Конечная точка {end} не найдена в графе");

            // Используем Манхэттенское расстояние по умолчанию
            heuristic ??= (a, b) => a.ManhattanDistance(b);

            // Открытый список (точки для исследования)
            var openSet = new PriorityQueue<Node, double>();

            // Закрытый список (уже исследованные точки)
            var closedSet = new HashSet<Coordinates>();

            // Для быстрого доступа к узлам
            var allNodes = new Dictionary<Coordinates, Node>();

            // Начинаем со стартовой точки
            var startNode = new Node(start)
            {
                G = 0,
                H = heuristic(start, end)
            };

            openSet.Enqueue(startNode, startNode.F);
            allNodes[start] = startNode;

            while (openSet.Count > 0)
            {
                // Берем узел с наименьшей F
                var currentNode = openSet.Dequeue();

                // Если достигли цели
                if (currentNode.Position.Equals(end))
                {
                    return ReconstructPath(currentNode);
                }

                // Добавляем в закрытый список
                closedSet.Add(currentNode.Position);

                foreach (var item in graph.Keys)
                {
                    Console.WriteLine(item);
                }
                // Проверяем всех соседей
                foreach (var neighborPos in graph[currentNode.Position])
                {
                    // Пропускаем если уже исследовали
                    if (closedSet.Contains(neighborPos))
                        continue;

                    // Вычисляем стоимость пути до соседа
                    // Предполагаем, что стоимость перехода = 1 (можно изменить)
                    double tentativeG = currentNode.G + 1;

                    // Получаем или создаем узел для соседа
                    if (!allNodes.TryGetValue(neighborPos, out var neighborNode))
                    {
                        neighborNode = new Node(neighborPos);
                        allNodes[neighborPos] = neighborNode;
                    }

                    // Если нашли лучший путь до соседа
                    if (tentativeG < neighborNode.G || neighborNode.G == 0)
                    {
                        neighborNode.Parent = currentNode;
                        neighborNode.G = tentativeG;
                        neighborNode.H = heuristic(neighborPos, end);

                        // Добавляем/обновляем в открытом списке
                        if (!openSet.UnorderedItems.Any(x => x.Element.Position.Equals(neighborPos)))
                        {
                            openSet.Enqueue(neighborNode, neighborNode.F);
                        }
                    }
                }
            }

            // Путь не найден
            return new List<Coordinates>();
        }

        /// <summary>
        /// Восстанавливает путь от конечного узла к начальному
        /// </summary>
        private List<Coordinates> ReconstructPath(Node endNode)
        {
            var path = new List<Coordinates>();
            var currentNode = endNode;

            while (currentNode != null)
            {
                path.Insert(0, currentNode.Position);
                currentNode = currentNode.Parent;
            }

            return path;
        }
    }
}
