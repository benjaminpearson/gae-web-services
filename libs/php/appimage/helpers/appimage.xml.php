<?php
// Source: http://snipplr.com/view/3491/convert-php-array-to-xml-or-simple-xml-object-if-you-wish/

class XMLHelper
{
	/**
	 * The main function for converting to an XML document.
	 * Pass in a multi dimensional array and this recursively loops through and builds up an XML document.
	 *
	 * @param array $data
	 * @param string $rootNodeName - what you want the root node to be - defaults to data.
	 * @param SimpleXMLElement $xml - should only be used recursively
	 * @return string XML
	 */
	public static function toXML($data, $rootNodeName = 'ResultSet', &$xml = null) {
		// turn off compatibility mode as simple xml throws a wobbly if you don't.
		if(ini_get('zend.ze1_compatibility_mode') == 1) {
			ini_set('zend.ze1_compatibility_mode', 0);
		}

		if(is_null($xml)) {
			$xml = simplexml_load_string("<?xml version='1.0' encoding='utf-8'?><$rootNodeName/>");
		}

		// loop through the data passed in.
		foreach($data as $key => $value) {
			// no numeric keys in our xml please!
			$numeric = 0;
			if(is_numeric($key)) {
				$numeric = 1;
				$key = $rootNodeName;
			}

			// delete any char not allowed in XML element names
			$key = preg_replace('/[^a-z0-9\-\_\.\:]/i', '', $key);

			// if there is another array found recrusively call this function
			if(is_array($value)) {
				$node = XMLHelper::isAssoc($value) || $numeric ? $xml->addChild($key) : $xml;

				// recrusive call.
				if($numeric) {
					$key = 'anon';
				}
				XMLHelper::toXml($value, $key, $node);
			} else {
				// add single node.
				$value = htmlentities($value);
				$xml->addChild($key, $value);
			}
		}

		// pass back as XML
		return $xml->asXML();
	}


	/**
	 * Convert an XML document to a multi dimensional array
	 * Pass in an XML document (or SimpleXMLElement object) and this recrusively loops through and builds a representative array
	 *
	 * @param string $xml - XML document - can optionally be a SimpleXMLElement object
	 * @return array ARRAY
	 */
	public static function toArray( $xml ) {
		if(is_string($xml)) {
			$xml = new SimpleXMLElement( $xml );
		}

		$children = $xml->children();

		if(!$children) {
			return (string) $xml;
		}

		$arr = array();
		foreach($children as $key => $node) {
			$node = XMLHelper::toArray($node);

			// support for 'anon' non-associative arrays
			if($key == 'anon') {
				$key = count($arr);
			}

			// ensures all keys are in lowercase underscore just for ease of use
			$key = XMLHelper::_fromCamelCase($key);

			// if the node is already set, put it into an array
			if(isset($arr[$key])) {
				if(!is_array($arr[$key]) || (isset($arr[$key][0]) && $arr[$key][0] == null)) {
					$arr[$key] = array( $arr[$key] );
				}
				$arr[$key][] = $node;
			} else {
				$arr[$key] = $node;
			}
		}
		return $arr;
	}

	// determine if a variable is an associative array
	public static function isAssoc( $array ) {
		return (is_array($array) && 0 !== count(array_diff_key($array, array_keys(array_keys($array)))));
	}

	/**
   * Translates a camel case string into a string with underscores (e.g. firstName = first_name)
	 * Source: http://www.paulferrett.com/2009/php-camel-case-functions/
	 *
   * @param   string  $str  String in camel case format
   * @return  string  $str  Translated into underscore format
   */
  private static function _fromCamelCase($str) {
		$str[0] = strtolower($str[0]);
		$func = create_function('$c', 'return "_" . strtolower($c[1]);');
		return preg_replace_callback('/([A-Z])/', $func, $str);
  }
}
?>