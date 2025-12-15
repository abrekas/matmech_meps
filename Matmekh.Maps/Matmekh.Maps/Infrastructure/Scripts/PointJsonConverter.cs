using System.Text.Json.Serialization;
using System.Text.Json;
using Matmekh.Maps.Domain.ValueTypes;

namespace Matmekh.Maps.Infrastructure.Scripts
{
    // Конвертер JSON для Point
    public class PointJsonConverter : JsonConverter<Coordinates>
    {
        public override Coordinates Read(
            ref Utf8JsonReader reader,
            Type typeToConvert,
            JsonSerializerOptions options)
        {
            var str = reader.GetString();
            return Coordinates.Parse(str!);
        }

        public override void Write(
            Utf8JsonWriter writer,
            Coordinates value,
            JsonSerializerOptions options)
        {
            writer.WriteStringValue($"{value.X},{value.Y}");
        }
    }
}
