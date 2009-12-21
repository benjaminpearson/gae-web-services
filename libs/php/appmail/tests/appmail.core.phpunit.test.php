<?php
/**
 * Tests for appmail.core.php
 * This test case is specific for PHPUnit and requires the phpunit PEAR package.
 * It allows you to easily debug the output of method calls and also validate that you config settings
 * are valid and working correctly.
 *
 * Command line: phpunit AppMailCoreTest appmail.core.phpunit.test.php
 */

require_once 'PHPUnit'.DIRECTORY_SEPARATOR.'Framework.php';
require_once '..'.DIRECTORY_SEPARATOR.'appmail.core.php';

class AppMailCoreTest extends PHPUnit_Framework_TestCase {
	var $AppMailCore;

	function setup() {
		$this->AppMailCore = new AppMailCore();
	}

	function testSend() {
		$to = "John Smith <john.smith@example.com>";
		$from = "John Smith <john.smith@example.com>"; // has to be a registered GAE email
		$subject = "Test email";
		$body = "This is a test message";
		$status = $this->AppMailCore->send($to, $from, $subject, $body);
		$this->assertEquals(sizeof($status), "Success");
		print_r($status);
	}
}
?>
