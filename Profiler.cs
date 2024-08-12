using System;
using System.Globalization;
using System.Collections.Generic;

public class Profiler_t
{
	public readonly struct eventEntry
    {
		public sbyte _id;
		public sbyte _value;
		public DateTime _time;

		public eventEntry(sbyte id, sbyte value)
        {
			this._id = id;
			this._value = value;
			this._time = DateTime.Now;
		}
	}

	public struct statEntry
    {
		uint _count;
		double _microseconds;

		statEntry()
        {
			this._count = 0;
			this._microseconds = 0;
        }

		void registerEvent(eventEntry start, eventEntry end)
        {
			assert(start._id == end._id);
			assert(end._value == 0);
			TimeSpan diffTime = end._time - start._time;
			++this._count;
			this._microseconds += diffTime.TotalMicroseconds;
		}
    }

	class Buffer
    {
		String _filename;
		List<eventEntry> _entries;
		
		public SortedDictionary<String, statEntry> getStats()
        {
			var result = new SortedDictionary<sbyte, statEntry>();
			var stack = new Stack<eventEntry>();

			foreach (eventEntry entry in this._entries)
			{
				if (entry._value != 0)
					stack.Push(entry);
				else
                {
					eventEntry start = stack.Pop();
					if (start._value != entry._value)
						throw new InvalidOperationException("Error in trace pair");

					const char id = entry._id;

					if (!result.ContainsKey(id))
						result.Add(id, statEntry());

					result[id].registerEvent(start, entry);
				}
			}

			return result;
		}

		public void generateTrace()
        {
			double totalDuration = (this._entries.Last()._time - this._entries.First()._time).TotalMicroseconds;

			var stats = this.getStats();

			using(var traceFile = new StreamWriter(this._filename))
            {
				foreach(var entry in stats)
                {
					double percent = entry.Value._microseconds * 100 / totalDuration;

					traceFile.WriteLine("# {0} {1} {2}", entry.Key, entry.Value, percent);
                }
            }
        }

		public buffer(String filename)
        {
			_filename = filename;
        }

		public void emplace(sbyte id, sbyte value)
        {
			_entries.Add(new eventEntry(id, value));
        }
		
    }

	sbyte _id;
	public static Buffer _profileBuffer; 

	public static Profiler_t(sbyte id, sbyte value = 0)
	{
		_id = id;
		if (value == 0)
			throw new InvalidOperationException("Error in trace constructor");

		_profileBuffer.emplace(_id, value);
	}

	public static done()
    {
		_profileBuffer.emplace(_id, 0);
    }

	public static Initialize()
    {
		_profileBuffer = new Buffer("Tracefile_old.txt");
    }

	public static Finalize()
    {
		_profileBuffer.generateTrace();

		_profileBuffer = null;
	}

}
