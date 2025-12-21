using NUnit.Framework;
using Matmekh.Maps.Domain.ValueTypes;

namespace Matmekh.Maps.Domain.FindPath.Tests
{
	[TestFixture]
	public class AStarTests
	{
		private AStar _aStar;

		[SetUp]
		public void SetUp() => _aStar = new AStar();

		[Test]
		public void FindPath_SimpleStraightLine_ReturnsCorrectPath()
		{
			var graph = new Dictionary<Coordinates, List<Coordinates>>
			{
				{ new(0, 0), new List<Coordinates> { new(0, 1) } },
				{ new(0, 1), new List<Coordinates> { new(0, 0), new(0, 2) } },
				{ new(0, 2), new List<Coordinates> { new(0, 1), new(0, 3) } },
				{ new(0, 3), new List<Coordinates> { new(0, 2) } }
			};

			var start = new Coordinates(0, 0);
			var end = new Coordinates(0, 3);

			var path = _aStar.FindPath(graph, start, end);

			Assert.Multiple(() =>
			{
				Assert.That(path, Has.Count.EqualTo(4));
				Assert.That(path[0], Is.EqualTo(start));
				Assert.That(path[1], Is.EqualTo(new Coordinates(0, 1)));
				Assert.That(path[2], Is.EqualTo(new Coordinates(0, 2)));
				Assert.That(path[3], Is.EqualTo(end));
			});
		}

		[Test]
		public void FindPath_StartNotInGraph_ThrowsArgumentException()
		{
			var graph = new Dictionary<Coordinates, List<Coordinates>>
			{
				{ new(0, 0), new List<Coordinates>() }
			};

			var start = new Coordinates(1, 1);
			var end = new Coordinates(0, 0);

			var exception = Assert.Throws<ArgumentException>(
				() => _aStar.FindPath(graph, start, end));

			Assert.That(exception.Message, Does.Contain("не найдена в графе"));
		}

		[Test]
		public async Task FindPath_ComplexGraph_PerformanceTest()
		{
			int size = 10;
			var graph = CreateGridGraph(size, size);
			var start = new Coordinates(0, 0);
			var end = new Coordinates(size - 1, size - 1);

			var task = Task.Run(() => _aStar.FindPath(graph, start, end));
			var completedTask = await Task.WhenAny(task, Task.Delay(1000));

			Assert.That(completedTask, Is.SameAs(task), "Тест превысил время выполнения");
			Assert.That(task.Result, Is.Not.Empty);
		}

		private static readonly TestCaseData[] PathTestCases =
		{
			new TestCaseData(new Coordinates(0, 0), new Coordinates(2, 2), 5)
				.SetName("Diagonal path in 3x3 grid"),
			new TestCaseData(new Coordinates(0, 0), new Coordinates(0, 3), 4)
				.SetName("Straight horizontal path"),
			new TestCaseData(new Coordinates(0, 0), new Coordinates(3, 0), 4)
				.SetName("Straight vertical path")
		};


		[Test]
		public void FindPath_EmptyGraph_ThrowsException()
		{
			var emptyGraph = new Dictionary<Coordinates, List<Coordinates>>();
			var start = new Coordinates(0, 0);
			var end = new Coordinates(1, 1);

			Assert.Throws<ArgumentException>(() =>
				_aStar.FindPath(emptyGraph, start, end));
		}

		private Dictionary<Coordinates, List<Coordinates>> CreateGridGraph(int width, int height)
		{
			var graph = new Dictionary<Coordinates, List<Coordinates>>();

			for (int x = 0; x < width; x++)
			{
				for (int y = 0; y < height; y++)
				{
					var neighbors = new List<Coordinates>();
					var current = new Coordinates(x, y);

					if (x > 0) neighbors.Add(new(x - 1, y));
					if (x < width - 1) neighbors.Add(new(x + 1, y));
					if (y > 0) neighbors.Add(new(x, y - 1));
					if (y < height - 1) neighbors.Add(new(x, y + 1));

					graph[current] = neighbors;
				}
			}

			return graph;
		}
	}
}