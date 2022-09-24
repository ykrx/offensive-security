<!-- Notes:
    ping -c1 -t1 '<ip>\\''
-->

<?php if (isset($_GET['ip'])) {
    $ip = $_GET['ip'];
    if (strpos($ip, " ")) {
        die("Spaces not allowed in the IP!");
    }
    $ip = str_replace("'", "\\'", $ip);
    $cmd = "ping -c1 -t1 '$ip'";
    if ($_GET['debug']) {echo "$cmd\n";}
    echo shell_exec($cmd);
    die();
}
?>

<html>

<body>

  <form method="GET">
    IP to ping: <input type="text" placeholder="IP" name="ip" />
    <input type="submit" value="Ping" />
  </form>
</body>

</html>