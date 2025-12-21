using NUnit.Framework;
using Moq;
using Matmekh.Maps.Domain.FindPath;
using Matmekh.Maps.Domain.Entities;
using Matmekh.Maps.Domain.ValueTypes;
using System;
using System.Collections.Generic;

namespace Matmekh.Maps.Domain.FindPath.Tests
{
	[TestFixture]
	public class PathFinderServiceSimpleTests
	{
		private Mock<ISearcher> _mockSearcher;
		private Mock<IGraph> _mockGraph;
		private PathFinderService _service;

		[SetUp]
		public void SetUp()
		{
			_mockSearcher = new Mock<ISearcher>();
			_mockGraph = new Mock<IGraph>();
			_service = new PathFinderService(_mockSearcher.Object, _mockGraph.Object);
		}

		[Test]
		public void FindPath_ValidNames_ReturnsRoute()
		{
			var startCab = new Cabinet("Аудитория101", new Coordinates(0, 0));
			var endCab = new Cabinet("Аудитория202", new Coordinates(2, 2));
			var expectedPath = new List<Coordinates>
			{
				new(0, 0),
				new(1, 1),
				new(2, 2)
			};

			SetupGraph(startCab, endCab);
			SetupSearcher(startCab.Location, endCab.Location, expectedPath);

			var result = _service.FindPath("Аудитория101", "Аудитория202");

			Assert.That(result.Start, Is.EqualTo(startCab));
			Assert.That(result.End, Is.EqualTo(endCab));
			Assert.That(result.Points, Is.EqualTo(expectedPath));
		}

		[Test]
		public void FindPath_StartNameNotFound_ThrowsException()
		{
			_mockGraph.Setup(g => g.Names)
				.Returns(new Dictionary<string, Cabinet>
				{
					{ "Аудитория202", new Cabinet("Аудитория202", new Coordinates(1, 1)) }
				});

			var ex = Assert.Throws<ArgumentException>(
				() => _service.FindPath("Несуществующий", "Аудитория202"));

			Assert.That(ex.Message, Does.Contain("Не найдена начальная точка"));
		}

		[Test]
		public void FindPath_EndNameNotFound_ThrowsException()
		{
			_mockGraph.Setup(g => g.Names)
				.Returns(new Dictionary<string, Cabinet>
				{
					{ "Аудитория101", new Cabinet("Аудитория101", new Coordinates(0, 0)) }
				});

			var ex = Assert.Throws<ArgumentException>(
				() => _service.FindPath("Аудитория101", "Несуществующий"));

			Assert.That(ex.Message, Does.Contain("Не найдена конечная точка"));
		}

		[Test]
		public void FindPath_NoPath_ReturnsEmptyRoute()
		{
			var startCab = new Cabinet("Аудитория101", new Coordinates(0, 0));
			var endCab = new Cabinet("Аудитория202", new Coordinates(5, 5));

			SetupGraph(startCab, endCab);
			SetupSearcher(startCab.Location, endCab.Location, new List<Coordinates>());

			var result = _service.FindPath("Аудитория101", "Аудитория202");

			Assert.That(result.Points, Is.Empty);
		}

		private void SetupGraph(Cabinet start, Cabinet end)
		{
			_mockGraph.Setup(g => g.Names)
				.Returns(new Dictionary<string, Cabinet>
				{
					{ start.Name, start },
					{ end.Name, end }
				});

			_mockGraph.Setup(g => g.GraphDictionary)
				.Returns(new Dictionary<Coordinates, List<Coordinates>>
				{
					{ start.Location, new List<Coordinates>() },
					{ end.Location, new List<Coordinates>() }
				});
		}

		private void SetupSearcher(Coordinates start, Coordinates end, List<Coordinates> path)
		{
			_mockSearcher.Setup(s => s.FindPath(
					It.IsAny<Dictionary<Coordinates, List<Coordinates>>>(),
					start,
					end,
					null))
				.Returns(path);
		}
	}
}