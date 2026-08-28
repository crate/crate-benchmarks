<details>
<summary><code>select "cCode", count(*) from uservisits group by "cCode";</code></summary>

```
# Results (server side duration in ms)
V1: 6.5.0-fcd878fc151e791062a0ad02850105fe450aceb3
V2: 6.5.0-b04172be55a9e38341fc43d49118723710749dd2

Q:     select "cCode", count(*) from uservisits group by "cCode";

C: 10
| Version |         Mean ±    Stdev |        Min |     Median |         Q3 |        Max |
|   V1    |       10.074 ±   41.508 |      1.460 |      4.907 |      8.286 |    476.939 |
|   V2    |        8.532 ±   38.364 |      1.225 |      4.301 |      6.557 |    438.898 |
├---------┴-------------------------┴------------┴------------┴------------┴------------┘
|               -  16.58%                           -  13.15%   
There is a 61.18% probability that the observed difference is not random, and the best estimate of that difference is 16.58%
The test has no statistical significance


System/JVM Metrics (durations in ms, byte-values in MB)
    |    YOUNG GC            |       OLD GC           |      HEAP         |     ALLOC     
    |  cnt      avg      max |  cnt      avg      max |  initial     used |     rate      total
 V1 |    0     0.00     0.00 |    0     0.00     0.00 |    17180        0 |   418.10        528
 V2 |    0     0.00     0.00 |    0     0.00     0.00 |    17180        0 |   419.40        430
    
Top allocation frames
  V1
    BytesRef.utf8ToString() total=144797088, count=37
    Long.valueOf(long) total=35282880, count=14
    Unsafe.allocateUninitializedArray(Class, int) total=23931128, count=51
    StringUTF16.compress(...) total=23598536, count=8
    ParserATNSimulator.getEpsilonTarget(...) total=23594313, count=37
    Unsafe.allocateInstance(Class) total=21489017, count=18
    DirectMethodHandle.allocateInstance(Object) total=20464505, count=21
    SegmentTermsEnumFrame.loadBlock() total=16190146, count=7
    SegmentTermsEnum.getFrame(int) total=14322104, count=4
    HashMap.newNode(...) total=13833376, count=11
  V2
    BytesRef.utf8ToString() total=84672504, count=25
    StringUTF16.compress(...) total=49639136, count=12
    ParserATNSimulator.getEpsilonTarget(...) total=35336737, count=44
    Unsafe.allocateUninitializedArray(Class, int) total=34602216, count=57
    Lucene104PostingsReader.newTermState() total=16774712, count=4
    HashMap.newNode(...) total=16413304, count=9
    String.encodeUTF8(...) total=12921224, count=32
    GroupByOptimizedIterator.getCountsByKey(...) total=12533746, count=15
    SegmentTermsEnum.<init>(...) total=8387200, count=2
    SegmentTermsEnum.getFrame(int) total=8245872, count=2

Top frames (by count)
  V1
    Unsafe.allocateUninitializedArray(Class, int) total=23931128, count=51
    ParserATNSimulator.getEpsilonTarget(...) total=23594313, count=37
    BytesRef.utf8ToString() total=144797088, count=37
    String.encodeUTF8(...) total=8045872, count=24
    DirectMethodHandle.allocateInstance(Object) total=20464505, count=21
    Unsafe.allocateInstance(Class) total=21489017, count=18
    Arrays.copyOf(...) total=4586699, count=17
    GroupByOptimizedIterator.getCountsByKey(...) total=16, count=16
    HashMap.resize() total=12202417, count=16
    ArrayList.grow(int) total=7571584, count=15
  V2
    Unsafe.allocateUninitializedArray(Class, int) total=34602216, count=57
    ParserATNSimulator.getEpsilonTarget(...) total=35336737, count=44
    String.encodeUTF8(...) total=12921224, count=32
    BytesRef.utf8ToString() total=84672504, count=25
    GroupByOptimizedIterator.getCountsByKey(...) total=12533746, count=15
    ArrayList.iterator() total=5788000, count=14
    ParserATNSimulator.closure_(...) total=12, count=12
    StringUTF16.compress(...) total=49639136, count=12
    BufferRecycler.calloc(int) total=7174576, count=11
    UnicodeUtil.UTF8toUTF16(...) total=11, count=11

perf stat
  v1
    branches        :   5531564677.00
    cache-misses    :    110053842.00
    instructions    :  27590526141.00
    faults          :         7191.00
    context-switches:        12072.00
  v2
    branches        :   5288363830.00
    cache-misses    :    109749052.00
    instructions    :  26133952206.00
    faults          :         8436.00
    context-switches:        11654.00
```

</details>

<details>
<summary><code>select "destinationURL", count(*) from uservisits group by "destinationURL";</code></summary>

```
# Results (server side duration in ms)
V1: 6.5.0-fcd878fc151e791062a0ad02850105fe450aceb3
V2: 6.5.0-b04172be55a9e38341fc43d49118723710749dd2

Q:     select "destinationURL", count(*) from uservisits group by "destinationURL";

C: 3
| Version |         Mean ±    Stdev |        Min |     Median |         Q3 |        Max |
|   V1    |     3850.772 ±  634.676 |   2751.985 |   3719.551 |   4129.168 |   6570.627 |
|   V2    |     3761.016 ±  585.873 |   2678.935 |   3656.510 |   4025.155 |   6232.694 |
├---------┴-------------------------┴------------┴------------┴------------┴------------┘
|               -   2.36%                           -   1.71%   
There is a 85.75% probability that the observed difference is not random, and the best estimate of that difference is 2.36%
The test has no statistical significance


System/JVM Metrics (durations in ms, byte-values in MB)
    |    YOUNG GC            |       OLD GC           |      HEAP         |     ALLOC     
    |  cnt      avg      max |  cnt      avg      max |  initial     used |     rate      total
 V1 |  303   229.94   212.82 |   33  1999.19  2197.27 |    17180     4719 |   714.13     219589
 V2 |  275   258.37   281.43 |   29  2344.56  2728.07 |    17180     3817 |   681.87     201005
    
Top allocation frames
  V1
    BytesRef.utf8ToString() total=98131460945, count=26973
    StringUTF16.compress(...) total=45402010634, count=12731
    HashMap.newNode(...) total=20933088144, count=5788
    DirectMethodHandle.allocateInstance(Object) total=17277127317, count=4590
    0x0000000092134000.apply(long) total=15896291823, count=5885
    HashMap.resize() total=15121153900, count=8783
    GroupingCollector.reduce(Map, Row) total=2985369171, count=8165
    CompositeBatchIterator$AsyncCompositeBI.lambda$loadNextBatch$0(int, int) total=1803536568, count=427
    AbstractQueuedSynchronizer$ConditionObject.newConditionNode() total=1054974512, count=141
    HashMap.replacementNode(...) total=370557528, count=27
  V2
    BytesRef.utf8ToString() total=99768827465, count=25901
    StringUTF16.compress(...) total=41874750698, count=12119
    HashMap.newNode(...) total=18952229292, count=5598
    HashMap.resize() total=15330613020, count=7762
    GroupByOptimizedIterator.getCountsByKey(...) total=14655373473, count=5004
    GroupingCollector.reduce(Map, Row) total=3881759887, count=7885
    CompositeBatchIterator$AsyncCompositeBI.lambda$loadNextBatch$0(int, int) total=3088782736, count=481
    AbstractQueuedSynchronizer$ConditionObject.newConditionNode() total=1766423160, count=168
    DirectMethodHandle.allocateInstance(Object) total=1199895328, count=258
    UnsafeByteBufUtil.newDirectByteBuf(...) total=217898848, count=94

Top frames (by count)
  V1
    BytesRef.utf8ToString() total=98131460945, count=26973
    HashMap.compute(...) total=13323, count=13323
    StringUTF16.compress(...) total=45402010634, count=12731
    HashMap.resize() total=15121153900, count=8783
    GroupingCollector.reduce(Map, Row) total=2985369171, count=8165
    0x0000000092134000.apply(long) total=15896291823, count=5885
    HashMap.newNode(...) total=20933088144, count=5788
    ImmutableCollections$MapN.probe(Object) total=5742, count=5742
    UnicodeUtil.UTF8toUTF16(...) total=5550, count=5550
    DirectMethodHandle.allocateInstance(Object) total=17277127317, count=4590
  V2
    BytesRef.utf8ToString() total=99768827465, count=25901
    HashMap.getNode(Object) total=13960, count=13960
    StringUTF16.compress(...) total=41874750698, count=12119
    GroupingCollector.reduce(Map, Row) total=3881759887, count=7885
    HashMap.resize() total=15330613020, count=7762
    HashMap.newNode(...) total=18952229292, count=5598
    NumberOutput.outputLong(...) total=5525, count=5525
    UnicodeUtil.UTF8toUTF16(...) total=5240, count=5240
    GroupByOptimizedIterator.getCountsByKey(...) total=14655373473, count=5004
    ReferencePipeline$3$1.accept(Object) total=3642, count=3642

perf stat
  v1
    branches        :   731709571202.00
    cache-misses    :    20225245363.00
    instructions    :  4225217165210.00
    faults          :       15077317.00
    context-switches:         583706.00
  v2
    branches        :   765564376490.00
    cache-misses    :    21129265811.00
    instructions    :  4451114536392.00
    faults          :       14936390.00
    context-switches:         547273.00
```

</details>
