import java.io.IOException;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.StringJoiner;
import java.util.stream.Stream;

import jdk.jfr.consumer.RecordedEvent;
import jdk.jfr.consumer.RecordedFrame;
import jdk.jfr.consumer.RecordedMethod;
import jdk.jfr.consumer.RecordedStackTrace;
import jdk.jfr.consumer.RecordingFile;


public class JfrOverview {

    private static double totalAllocated;
    private static long firstAllocationTime = -1;

    static class DoubleMeasure {

        private int count = 0;
        private double total;
        private double max;
        private double value;

        public double getAverage() {
            return total / count;
        }

        public void add(double value) {
            this.count++;
            this.total += value;
            this.max = Math.max(this.value, value);
            this.value = value;
        }

        @Override
        public String toString() {
            return "DoubleMeasure{count=" + count + ", max=" + max + ", total=" + total + ", value=" + value + "}";
        }
    }

    static class LongMeasure {

        private int count = 0;
        private long total;
        private long max;
        private long value;

        public LongMeasure() {
            this.count = 0;
            this.total = 0;
            this.max = 0;
            this.value = 0;
        }

        public LongMeasure(long value) {
            this.count = 1;
            this.total += value;
            this.max = value;
            this.value = value;
        }

        public double getAverage() {
            if (count == 0) {
                return total;
            }
            return total / count;
        }

        public void add(long value) {
            this.count++;
            this.total += value;
            this.max = Math.max(this.value, value);
            this.value = value;
        }
    }


    private static List<String> decodeDescriptors(String descriptor) {
        List<String> descriptors = new ArrayList<>();
        for (int index = 0; index < descriptor.length(); index++) {
            String arrayBrackets = "";
            while (descriptor.charAt(index) == '[') {
                arrayBrackets += "[]";
                index++;
            }
            char c = descriptor.charAt(index);
            String type;
            switch (c) {
            case 'L':
                int endIndex = descriptor.indexOf(';', index);
                type = descriptor.substring(index + 1, endIndex);
                index = endIndex;
                break;
            case 'I':
                type = "int";
                break;
            case 'J':
                type = "long";
                break;
            case 'Z':
                type = "boolean";
                break;
            case 'D':
                type = "double";
                break;
            case 'F':
                type = "float";
                break;
            case 'S':
                type = "short";
                break;
            case 'C':
                type = "char";
                break;
            case 'B':
                type = "byte";
                break;
            default:
                type = "<unknown-descriptor-type>";
            }
            descriptors.add(type + arrayBrackets);
        }
        return descriptors;
    }

    private static String formatMethod(RecordedMethod m) {
        StringBuilder sb = new StringBuilder();
        String typeName = m.getType().getName();
        typeName = typeName.substring(typeName.lastIndexOf('.') + 1);
        sb.append(typeName).append(".").append(m.getName());
        sb.append("(");
        StringJoiner sj = new StringJoiner(", ");
        String md = m.getDescriptor().replace("/", ".");
        String parameter = md.substring(1, md.lastIndexOf(")"));
        for (String qualifiedName : decodeDescriptors(parameter)) {
            sj.add(qualifiedName.substring(qualifiedName.lastIndexOf('.') + 1));
        }
        sb.append(sj.length() > 10 ? "..." : sj);
        sb.append(")");
        return sb.toString();
    }

    private static String topFrame(RecordedStackTrace stackTrace) {
        if (stackTrace == null) {
            return null;
        }
        List<RecordedFrame> frames = stackTrace.getFrames();
        if (!frames.isEmpty()) {
            RecordedFrame topFrame = frames.get(0);
            if (topFrame.isJavaFrame()) {
                return formatMethod(topFrame.getMethod());
            }
        }
        return null;
    }

    public static record Record(String name, int count, long value, long total) {

        String format() {
            return "\"" + name + " total=" + total + ", count=" + count + "\"";
        }
    }

    static class Histogram {

        private static final HashMap<String, LongMeasure> histogram = new HashMap<>();

        public void add(String key, long value) {
            var measure = histogram.get(key);
            if (measure == null) {
                measure = new LongMeasure();
                histogram.put(key, measure);
            }
            measure.add(value);
        }

        public List<Record> getRecords() {
            ArrayList<Record> values = new ArrayList<>();
            for (var e : histogram.entrySet()) {
                var measure = e.getValue();
                values.add(new Record(e.getKey(), measure.count, measure.value, measure.total));
            }
            return values;
        }

        public Stream<Record> byTotal() {
            return getRecords()
                .stream()
                .sorted(Comparator.comparingLong(Record::total).reversed())
                .limit(10);
        }

        public Stream<Record> byCount() {
            return getRecords()
                .stream()
                .sorted(Comparator.comparingLong(Record::count).reversed())
                .limit(10);
        }
    }

    private static final LongMeasure ALLOC_TOTAL = new LongMeasure();
    private static final DoubleMeasure ALLOC_RATE = new DoubleMeasure();
    private static final Histogram ALLOCATION_TOP_FRAME = new Histogram();

    private static void onAllocationSample(RecordedEvent event, long size) {
        String topFrame = topFrame(event.getStackTrace());
        if (topFrame != null) {
            ALLOCATION_TOP_FRAME.add(topFrame, size);
        }
        ALLOC_TOTAL.add(size);
        long timestamp = event.getEndTime().toEpochMilli();
        totalAllocated += size;
        if (firstAllocationTime > 0) {
            long elapsedTime = timestamp - firstAllocationTime;
            if (elapsedTime > 0) {
                double rate = 1000.0 * (totalAllocated / elapsedTime);
                ALLOC_RATE.add(rate);
            }
        } else {
            firstAllocationTime = timestamp;
        }
    }

    public static void main(String[] args) throws IOException {
        if (args.length < 1) {
            throw new IllegalArgumentException("Path to JFR recording required");
        }
        var recordingFile = new RecordingFile(Paths.get(args[0]));

        DoubleMeasure machineCpu = new DoubleMeasure();
        DoubleMeasure jvmSystem = new DoubleMeasure();
        DoubleMeasure jvmUser = new DoubleMeasure();
        LongMeasure youngGc = new LongMeasure();
        LongMeasure oldGc = new LongMeasure();
        LongMeasure usedHeap = new LongMeasure();
        LongMeasure physicalMemory = new LongMeasure();
        DoubleMeasure threads = new DoubleMeasure();
        LongMeasure classes = new LongMeasure();
        LongMeasure compilation = new LongMeasure();
        LongMeasure initialHeap = new LongMeasure();
        Histogram executionTopFrame = new Histogram();
        String gcName = "Unknown";

        while (recordingFile.hasMoreEvents()) {
            var event = recordingFile.readEvent();
            switch (event.getEventType().getName()) {
                case "jdk.CPULoad" -> {
                    machineCpu.add(event.getDouble("machineTotal"));
                    jvmSystem.add(event.getDouble("jvmSystem"));
                    jvmUser.add(event.getDouble("jvmUser"));
                }
                case "jdk.YoungGarbageCollection" -> {
                    long nanos = event.getDuration().toNanos();
                    youngGc.add(nanos);
                }
                case "jdk.OldGarbageCollection" -> {
                    long nanos = event.getDuration().toNanos();
                    oldGc.add(nanos);
                }
                case "jdk.GCHeapSummary" -> {
                    usedHeap.add(event.getLong("heapUsed"));
                }
                case "jdk.PhysicalMemory" -> {
                    physicalMemory.add(event.getLong("totalSize"));
                }
                case "jdk.GCConfiguration" -> {
                    String gc = event.getString("oldCollector");
                    String yc = event.getString("youngCollector");
                    if (yc != null) {
                        gc += "/" + yc;
                    }
                    gcName = gc;
                }
                case "jdk.ObjectAllocationOutsideTLAB" -> {
                    onAllocationSample(event, event.getLong("allocationSize"));
                }
                case "jdk.ObjectAllocationInNewTLAB" -> {
                    onAllocationSample(event, event.getLong("tlabSize"));
                }
                case "jdk.ExecutionSample" -> {
                    String topFrame = topFrame(event.getStackTrace());
                    executionTopFrame.add(topFrame, 1);
                }
                case "jdk.JavaThreadStatistics" -> {
                    threads.add(event.getDouble("activeCount"));
                }
                case "jdk.ClassLoadingStatistics" -> {
                    long diff = event.getLong("loadedClassCount") - event.getLong("unloadedClassCount");
                    classes.add(diff);
                }
                case "jdk.Compilation" -> {
                    compilation.add(event.getDuration().toNanos());
                }
                case "jdk.GCHeapConfiguration" -> {
                    initialHeap.add(event.getLong("initialSize"));
                }
            }
        }
        String jsonResult = String.format(Locale.ENGLISH,
            """
            {
                "gc": {
                    "name": "%s",
                    "young": {
                        "count": %s,
                        "max_duration_ns": %s,
                        "avg_duration_ns": %s
                    },
                    "old": {
                        "count": %s,
                        "max_duration_ns": %s,
                        "avg_duration_ns": %s
                    }
                },
                "cpu": {
                    "system": %s,
                    "jvm_user": %s,
                    "jvm_system": %s
                },
                "heap": {
                    "initial": %s,
                    "used": %s
                },
                "alloc": {
                    "rate": %s,
                    "total": %s,
                    "top_frames_by_count": %s,
                    "top_frames_by_alloc": %s
                },
                "threads": %s,
                "classes": %s
            }
            """,
            gcName,
            youngGc.count,
            youngGc.max,
            youngGc.getAverage(),
            oldGc.count,
            oldGc.max,
            oldGc.getAverage(),
            machineCpu.getAverage(),
            jvmUser.getAverage(),
            jvmSystem.getAverage(),
            initialHeap.value,
            usedHeap.value,
            ALLOC_RATE.value,
            ALLOC_TOTAL.total,
            '[' + String.join(", ", ALLOCATION_TOP_FRAME.byCount().map(Record::format).toArray(String[]::new)) + ']',
            '[' + String.join(", ", ALLOCATION_TOP_FRAME.byTotal().map(Record::format).toArray(String[]::new)) + ']',
            threads.value,
            classes.value
        );
        System.out.println(jsonResult);
    }
}
