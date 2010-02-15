<?php
/**
 * Tests for appimage.core.php
 * This test case is specific for PHPUnit and requires the phpunit PEAR package.
 * It allows you to easily debug the output of method calls and also validate that you config settings
 * are valid and working correctly.
 *
 * Command line: phpunit AppImageCoreTest appimage.core.phpunit.test.php
 */

require_once 'PHPUnit'.DIRECTORY_SEPARATOR.'Framework.php';
require_once '..'.DIRECTORY_SEPARATOR.'appimage.core.php';

class AppImageCoreTest extends PHPUnit_Framework_TestCase {
	var $AppImageCore;
	var $big_file = 'big.jpg';
	var $small_file = 'small.jpg';
	var $big_img_id = 'testopensourcebig';
	var $small_img_id = 'testopensourcesmall';

	function setup() {
		$this->AppImageCore = new AppImageCore();
	}

	function testUploadAvatarSmall() {
		$response = $this->AppImageCore->upload('avatar', $this->small_file, filesize($this->small_file), $this->small_img_id);

		$this->assertTrue(!empty($response));
		$urls = $this->AppImageCore->getUrls('avatar', $this->small_img_id);
		$this->assertEquals(md5(file_get_contents($urls['source'])),"5ad7d3f96b182d3770b1cd56339e8131");
	}

	function testUploadAvatarBig() {
		$response = $this->AppImageCore->upload('avatar', $this->big_file, filesize($this->big_file), $this->big_img_id);

		$this->assertTrue(!empty($response));
		$urls = $this->AppImageCore->getUrls('avatar', $this->big_img_id);
		$this->assertEquals(md5(file_get_contents($urls['source'])),"ffd83af30f249186488f2d819f29b09b");
	}

	function testUploadPhoto() {
		$response = $this->AppImageCore->upload('photo', $this->big_file, filesize($this->big_file), $this->big_img_id);

		$this->assertTrue(!empty($response));
		$urls = $this->AppImageCore->getUrls('photo', $this->big_img_id);
		$this->assertEquals(md5(file_get_contents($urls['source'])),"67199e0cb90eb8d6ff22a6c4a1a5f468");
	}

	function testGetUrlsAvatar() {
		$response = $this->AppImageCore->getUrls('avatar', $this->small_img_id);
		//print_r($response);
	}

	function testGetUrlsPhoto() {
		$response = $this->AppImageCore->getUrls('photo', $this->small_img_id);
		//print_r($response);
	}

	function testCropPercentage() {
		$x1 = 0.1;
		$y1 = 0.2;
		$x2 = 0.5;
		$y2 = 0.8;
		$unit = "percentage";
		$response = $this->AppImageCore->crop('avatar', $this->small_img_id, $x1, $y1, $x2, $y2, $unit);

		$this->assertTrue(!empty($response));
		$urls = $this->AppImageCore->getUrls('avatar', $this->small_img_id);
		$this->assertEquals(md5(file_get_contents($urls['image'])),"58bd13d32e8101645c293cdeff0a5ec1");
	}

	function testCropPixels() {
		$x1 = 20;
		$y1 = 80;
		$x2 = 260;
		$y2 = 300;
		$unit = "pixels";
		$response = $this->AppImageCore->crop('avatar', $this->small_img_id, $x1, $y1, $x2, $y2, $unit);

		$this->assertTrue(!empty($response));
		$urls = $this->AppImageCore->getUrls('avatar', $this->small_img_id);
		$this->assertEquals(md5(file_get_contents($urls['image'])),"5353c2b9ad9e60cd9ecbe921dab2184f");
	}

	function testResizePercentage() {
		// note: keeps aspect ratio, using dimensions that produce smallest image.
		// using the image provided will result in 123 x 154px image.
		$width = 0.4;
		$height = 0.5;
		$unit = "percentage";
		$response = $this->AppImageCore->resize('avatar', $this->small_img_id, $width, $height, $unit);

		$this->assertTrue(!empty($response));
		$urls = $this->AppImageCore->getUrls('avatar', $this->small_img_id);
		$this->assertEquals(md5(file_get_contents($urls['image'])),"7689c434fa853d0a9460c3a28cef0ebb");
	}

	function testResizePixels() {
		// note: keeps aspect ratio, using dimensions that produce smallest image.
		// using the image provided will result in 160 x 200px image.
		$width = 300;
		$height = 200;
		$unit = "pixels";
		$response = $this->AppImageCore->resize('avatar', $this->small_img_id, $width, $height, $unit);

		$this->assertTrue(!empty($response));
		$urls = $this->AppImageCore->getUrls('avatar', $this->small_img_id);
		$this->assertEquals(md5(file_get_contents($urls['image'])),"ed7c7e03524889af6f94b9bfb811b4ae");
	}
}
?>
