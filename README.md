import java.io.*;
import java.nio.file.*;
import java.security.*;
import java.util.*;

/**
 * JAR包SHA1比较工具
 * 用于比较两个文件夹中的JAR文件SHA1值差异
 */
public class JarSha1Comparator {

    /**
     * 主方法 - 程序入口
     * @param args 命令行参数：文件夹1路径 文件夹2路径
     */
    public static void main(String[] args) {
        // 步骤1: 验证输入参数
//        if (args.length != 2) {
//            System.err.println("使用方法: java JarSha1Comparator <文件夹1路径> <文件夹2路径>");
//            System.exit(1);
//        }
//
//        String folder1Path = args[0];
//        String folder2Path = args[1];
        String folder1Path = "D:\\dev\\Java\\JavaRepository\\ai\\djl\\api\\0.31.1";
        String folder2Path = "D:\\dev\\Java\\JavaRepository\\ai\\djl\\api\\0.31.1";

        try {
            // 步骤2: 执行比较并获取结果
            List<JarComparisonResult> differences = compareJarFolders(folder1Path, folder2Path);

            // 步骤3: 输出比较结果
            printComparisonResults(differences);

        } catch (Exception e) {
            System.err.println("比较过程中发生错误: " + e.getMessage());
            e.printStackTrace();
        }
    }

    /**
     * 比较两个文件夹中的JAR文件
     */
    public static List<JarComparisonResult> compareJarFolders(String folder1Path, String folder2Path)
            throws IOException, NoSuchAlgorithmException {

        // 步骤4: 验证文件夹存在性和可访问性
        validateFolder(folder1Path);
        validateFolder(folder2Path);

        // 步骤5: 扫描两个文件夹中的JAR文件
        System.out.println("开始扫描文件夹: " + folder1Path);
        Map<String, File> jarFiles1 = scanJarFiles(folder1Path);

        System.out.println("开始扫描文件夹: " + folder2Path);
        Map<String, File> jarFiles2 = scanJarFiles(folder2Path);

        // 步骤6: 计算所有JAR文件的SHA1值
        System.out.println("计算文件夹1中JAR文件的SHA1值...");
        Map<String, String> sha1Map1 = calculateAllSha1(jarFiles1);

        System.out.println("计算文件夹2中JAR文件的SHA1值...");
        Map<String, String> sha1Map2 = calculateAllSha1(jarFiles2);

        // 步骤7: 比较SHA1值并找出差异
        return findDifferences(sha1Map1, sha1Map2, jarFiles1, jarFiles2);
    }

    /**
     * 步骤4: 验证文件夹有效性
     */
    private static void validateFolder(String folderPath) {
        Path path = Paths.get(folderPath);

        // 检查路径是否存在
        if (!Files.exists(path)) {
            throw new IllegalArgumentException("文件夹不存在: " + folderPath);
        }

        // 检查是否为目录
        if (!Files.isDirectory(path)) {
            throw new IllegalArgumentException("路径不是文件夹: " + folderPath);
        }

        // 检查是否可读
        if (!Files.isReadable(path)) {
            throw new IllegalArgumentException("文件夹不可读: " + folderPath);
        }

        System.out.println("文件夹验证通过: " + folderPath);
    }

    /**
     * 步骤5: 扫描文件夹中的JAR文件
     */
    private static Map<String, File> scanJarFiles(String folderPath) throws IOException {
        Map<String, File> jarFiles = new HashMap<>();
        Path folder = Paths.get(folderPath);

        // 使用Files.walk遍历所有文件（包括子目录）
        Files.walk(folder)
                .filter(path -> {
                    // 步骤5.1: 过滤出JAR文件
                    String fileName = path.getFileName().toString().toLowerCase();
                    return fileName.endsWith(".jar") && Files.isRegularFile(path);
                })
                .forEach(jarPath -> {
                    // 步骤5.2: 获取相对路径作为键（避免绝对路径差异影响比较）
                    String relativePath = folder.relativize(jarPath).toString();
                    jarFiles.put(relativePath, jarPath.toFile());
                    System.out.println("发现JAR文件: " + relativePath);
                });

        System.out.println("在文件夹 " + folderPath + " 中共找到 " + jarFiles.size() + " 个JAR文件");
        return jarFiles;
    }

    /**
     * 步骤6: 批量计算JAR文件的SHA1值
     */
    private static Map<String, String> calculateAllSha1(Map<String, File> jarFiles)
            throws IOException, NoSuchAlgorithmException {

        Map<String, String> sha1Map = new HashMap<>();

        for (Map.Entry<String, File> entry : jarFiles.entrySet()) {
            String relativePath = entry.getKey();
            File jarFile = entry.getValue();

            try {
                // 步骤6.1: 计算单个JAR文件的SHA1
                String sha1 = calculateJarSha1(jarFile);
                sha1Map.put(relativePath, sha1);
                System.out.println("计算SHA1完成: " + relativePath + " -> " + sha1);

            } catch (IOException e) {
                System.err.println("计算SHA1失败: " + relativePath + " - " + e.getMessage());
                // 标记为错误状态
                sha1Map.put(relativePath, "ERROR: " + e.getMessage());
            }
        }

        return sha1Map;
    }

    /**
     * 步骤6.1: 计算单个JAR文件的SHA1值
     */
    private static String calculateJarSha1(File jarFile) throws IOException, NoSuchAlgorithmException {
        // 步骤6.1.1: 初始化SHA1消息摘要
        MessageDigest digest = MessageDigest.getInstance("SHA-1");

        // 步骤6.1.2: 使用缓冲流读取文件内容
        try (FileInputStream fis = new FileInputStream(jarFile);
             BufferedInputStream bis = new BufferedInputStream(fis)) {

            byte[] buffer = new byte[8192]; // 8KB缓冲区
            int bytesRead;

            // 步骤6.1.3: 逐块读取文件并更新摘要
            while ((bytesRead = bis.read(buffer)) != -1) {
                digest.update(buffer, 0, bytesRead);
            }
        }

        // 步骤6.1.4: 完成哈希计算并转换为十六进制字符串
        byte[] hashBytes = digest.digest();
        return bytesToHex(hashBytes);
    }

    /**
     * 将字节数组转换为十六进制字符串
     */
    private static String bytesToHex(byte[] bytes) {
        StringBuilder hexString = new StringBuilder();
        for (byte b : bytes) {
            String hex = Integer.toHexString(0xff & b);
            if (hex.length() == 1) {
                hexString.append('0');
            }
            hexString.append(hex);
        }
        return hexString.toString();
    }

    /**
     * 步骤7: 找出SHA1值不同的JAR文件
     */
    private static List<JarComparisonResult> findDifferences(
            Map<String, String> sha1Map1,
            Map<String, String> sha1Map2,
            Map<String, File> jarFiles1,
            Map<String, File> jarFiles2) {

        List<JarComparisonResult> differences = new ArrayList<>();
        Set<String> allJarNames = new HashSet<>();

        // 步骤7.1: 收集所有JAR文件名
        allJarNames.addAll(sha1Map1.keySet());
        allJarNames.addAll(sha1Map2.keySet());

        System.out.println("开始比较 " + allJarNames.size() + " 个JAR文件...");

        // 步骤7.2: 逐个比较JAR文件
        for (String jarName : allJarNames) {
            String sha11 = sha1Map1.get(jarName);
            String sha12 = sha1Map2.get(jarName);

            // 步骤7.3: 检查各种差异情况
            if (sha11 == null && sha12 != null) {
                // 情况1: 只在文件夹2中存在
                differences.add(new JarComparisonResult(
                        jarName, null, sha12,
                        DifferenceType.ONLY_IN_FOLDER2,
                        null, jarFiles2.get(jarName).getAbsolutePath()
                ));

            } else if (sha11 != null && sha12 == null) {
                // 情况2: 只在文件夹1中存在
                differences.add(new JarComparisonResult(
                        jarName, sha11, null,
                        DifferenceType.ONLY_IN_FOLDER1,
                        jarFiles1.get(jarName).getAbsolutePath(), null
                ));

            } else if (sha11 != null && sha12 != null) {
                // 情况3: 在两个文件夹中都存在，但SHA1值不同
                if (!sha11.equals(sha12)) {
                    differences.add(new JarComparisonResult(
                            jarName, sha11, sha12,
                            DifferenceType.SHA1_MISMATCH,
                            jarFiles1.get(jarName).getAbsolutePath(),
                            jarFiles2.get(jarName).getAbsolutePath()
                    ));
                }
            }
        }

        return differences;
    }

    /**
     * 步骤8: 打印比较结果
     */
    private static void printComparisonResults(List<JarComparisonResult> differences) {
        System.out.println("\n" + "=".repeat(80));
        System.out.println("JAR文件SHA1比较结果");
        System.out.println("=".repeat(80));

        if (differences.isEmpty()) {
            System.out.println("✓ 所有JAR文件的SHA1值都相同！");
            return;
        }

        // 按差异类型分组
        Map<DifferenceType, List<JarComparisonResult>> groupedDifferences = new HashMap<>();
        for (JarComparisonResult result : differences) {
            groupedDifferences
                    .computeIfAbsent(result.differenceType, k -> new ArrayList<>())
                    .add(result);
        }

        // 步骤8.1: 输出SHA1不匹配的JAR
        List<JarComparisonResult> sha1Mismatches = groupedDifferences.get(DifferenceType.SHA1_MISMATCH);
        if (sha1Mismatches != null && !sha1Mismatches.isEmpty()) {
            System.out.println("\n❌ SHA1值不同的JAR文件:");
            for (JarComparisonResult diff : sha1Mismatches) {
                System.out.println("   文件: " + diff.jarName);
                System.out.println("   文件夹1 SHA1: " + diff.sha1Folder1);
                System.out.println("   文件夹2 SHA1: " + diff.sha1Folder2);
                System.out.println("   文件夹1路径: " + diff.absolutePath1);
                System.out.println("   文件夹2路径: " + diff.absolutePath2);
                System.out.println("   " + "-".repeat(60));
            }
        }

        // 步骤8.2: 输出只在文件夹1中存在的JAR
        List<JarComparisonResult> onlyInFolder1 = groupedDifferences.get(DifferenceType.ONLY_IN_FOLDER1);
        if (onlyInFolder1 != null && !onlyInFolder1.isEmpty()) {
            System.out.println("\n📁 只在文件夹1中存在的JAR文件:");
            for (JarComparisonResult diff : onlyInFolder1) {
                System.out.println("   文件: " + diff.jarName);
                System.out.println("   路径: " + diff.absolutePath1);
            }
        }

        // 步骤8.3: 输出只在文件夹2中存在的JAR
        List<JarComparisonResult> onlyInFolder2 = groupedDifferences.get(DifferenceType.ONLY_IN_FOLDER2);
        if (onlyInFolder2 != null && !onlyInFolder2.isEmpty()) {
            System.out.println("\n📁 只在文件夹2中存在的JAR文件:");
            for (JarComparisonResult diff : onlyInFolder2) {
                System.out.println("   文件: " + diff.jarName);
                System.out.println("   路径: " + diff.absolutePath2);
            }
        }

        System.out.println("\n总计发现 " + differences.size() + " 个差异");
    }

    /**
     * JAR比较结果类
     */
    static class JarComparisonResult {
        String jarName;          // JAR文件相对路径名
        String sha1Folder1;      // 文件夹1中的SHA1值
        String sha1Folder2;      // 文件夹2中的SHA1值
        DifferenceType differenceType; // 差异类型
        String absolutePath1;    // 文件夹1中的绝对路径
        String absolutePath2;    // 文件夹2中的绝对路径

        public JarComparisonResult(String jarName, String sha1Folder1, String sha1Folder2,
                                   DifferenceType differenceType, String absolutePath1, String absolutePath2) {
            this.jarName = jarName;
            this.sha1Folder1 = sha1Folder1;
            this.sha1Folder2 = sha1Folder2;
            this.differenceType = differenceType;
            this.absolutePath1 = absolutePath1;
            this.absolutePath2 = absolutePath2;
        }
    }

    /**
     * 差异类型枚举
     */
    enum DifferenceType {
        SHA1_MISMATCH,   // SHA1值不同
        ONLY_IN_FOLDER1, // 只在文件夹1中存在
        ONLY_IN_FOLDER2  // 只在文件夹2中存在
    }
}
