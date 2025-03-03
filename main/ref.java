import java.util.*;

class Commit {
    String committerName;
    Date commitDate;

    public Commit(String committerName, Date commitDate) {
        this.committerName = committerName;
        this.commitDate = commitDate;
    }
}

public class WeeklyCommitCheck {
    public static void main(String[] args) {
        // List of all expected users
        List<String> users = Arrays.asList("Alice", "Bob", "Charlie", "David");

        // List of all commits ever made (unordered)
        List<Commit> commits = Arrays.asList(
            new Commit("Alice", getDateDaysAgo(3)),  // Alice committed 3 days ago
            new Commit("Alice", getDateDaysAgo(10)), // Alice committed 10 days ago (gap > 7 days)
            new Commit("Bob", getDateDaysAgo(5)),  // Bob committed 5 days ago
            new Commit("Bob", getDateDaysAgo(12)), // Bob committed 12 days ago (gap > 7 days)
            new Commit("Charlie", getDateDaysAgo(2)), // Charlie committed 2 days ago
            new Commit("Charlie", getDateDaysAgo(7)), // Charlie committed 7 days ago
            new Commit("Charlie", getDateDaysAgo(14)), // Charlie committed 14 days ago (no gap > 7 days)
            new Commit("David", getDateDaysAgo(1))  // David committed 1 day ago
        );

        // Find users who have a gap of more than 7 days between consecutive commits
        Set<String> irregularCommitters = findIrregularCommitters(users, commits);
        System.out.println("Users who do not commit every 7 days: " + irregularCommitters);
    }

    public static Set<String> findIrregularCommitters(List<String> users, List<Commit> commits) {
        // Store last commit date for each user
        Map<String, Date> lastCommitMap = new HashMap<>();
        Set<String> irregularCommitters = new HashSet<>();

        // Sort commits by date (important for tracking gaps correctly)
        commits.sort(Comparator.comparing(commit -> commit.commitDate));

        // Traverse commit list once
        for (Commit commit : commits) {
            if (lastCommitMap.containsKey(commit.committerName)) {
                long daysGap = getDaysBetween(lastCommitMap.get(commit.commitDate), commit.commitDate);
                if (daysGap > 7) {
                    irregularCommitters.add(commit.committerName);
                }
            }
            lastCommitMap.put(commit.committerName, commit.commitDate);
        }

        // Add users who never committed at all
        for (String user : users) {
            if (!lastCommitMap.containsKey(user)) {
                irregularCommitters.add(user);
            }
        }

        return irregularCommitters;
    }

    private static Date getDateDaysAgo(int days) {
        Calendar cal = Calendar.getInstance();
        cal.add(Calendar.DAY_OF_MONTH, -days);
        return cal.getTime();
    }

    private static long getDaysBetween(Date d1, Date d2) {
        return Math.abs((d2.getTime() - d1.getTime()) / (1000 * 60 * 60 * 24));
    }
}
