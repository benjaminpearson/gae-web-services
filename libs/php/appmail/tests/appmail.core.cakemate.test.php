<?php
/**
 * Tests for appmail.core.php
 * This test case is specific for CakePHP and requires CakeMate (Textmate plugin) in order to be run.
 * It allows you to easily debug the output of method calls and also validate that you config settings
 * are valid and working correctly.
 *
 * CakeMate URL: http://mark-story.com/posts/view/running-cakephp-unit-tests-with-textmate
 */

require_once('..'.DIRECTORY_SEPARATOR.'appmail.core.php');

class AppMailCoreTest extends UnitTestCase {
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
		$this->assertEqual(sizeof($status), "Success");
		debug($status);
	}
}
?>
