<?php
    $db=new SQLite3('playlist.db');
    $nsig = shell_exec("python2 playlist.py sig2");
    if ($nsig) {
        $query = $db->exec('DELETE FROM sig');
        $query = $db->exec("INSERT INTO sig (sig,time) VALUES ('".$nsig."', '".time()."')");
        if(!isset($query)) { exit; }
        echo "$nsig";
    } else { exit; }
?>
