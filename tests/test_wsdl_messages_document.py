from lxml import etree
from six import StringIO

from tests.utils import assert_nodes_equal, load_xml
from zeep import xsd
from zeep.wsdl import wsdl


def test_parse():
    wsdl_content = StringIO("""
    <definitions xmlns="http://schemas.xmlsoap.org/wsdl/"
                 xmlns:tns="http://tests.python-zeep.org/tns"
                 xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
                 xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                 targetNamespace="http://tests.python-zeep.org/tns">
      <types>
        <xsd:schema targetNamespace="http://tests.python-zeep.org/tns">
          <xsd:element name="Request" type="xsd:string"/>
          <xsd:element name="Response" type="xsd:string"/>
        </xsd:schema>
      </types>

      <message name="Input">
        <part element="tns:Request"/>
      </message>
      <message name="Output">
        <part element="tns:Response"/>
      </message>

      <portType name="TestPortType">
        <operation name="TestOperation">
          <input message="Input"/>
          <output message="Output"/>
        </operation>
      </portType>

      <binding name="TestBinding" type="tns:TestPortType">
        <soap:binding style="document" transport="http://schemas.xmlsoap.org/soap/http"/>
        <operation name="TestOperation">
          <soap:operation soapAction=""/>
          <input>
            <soap:body use="literal"/>
          </input>
          <output>
            <soap:body use="literal"/>
          </output>
        </operation>
      </binding>
    </definitions>
    """.strip())

    root = wsdl.Document(wsdl_content, None)

    binding = root.bindings['{http://tests.python-zeep.org/tns}TestBinding']
    operation = binding.get('TestOperation')

    assert operation.input.body.signature() == 'xsd:string'
    assert operation.input.header.signature() == ''
    assert operation.input.envelope.signature() == 'body: xsd:string, header: {}'
    assert operation.input.signature(as_output=False) == 'xsd:string'

    assert operation.output.body.signature() == 'xsd:string'
    assert operation.output.header.signature() == ''
    assert operation.output.envelope.signature() == 'body: xsd:string, header: {}'
    assert operation.output.signature(as_output=True) == 'body: xsd:string, header: {}'


def test_parse_with_header():
    wsdl_content = StringIO("""
    <definitions xmlns="http://schemas.xmlsoap.org/wsdl/"
                 xmlns:tns="http://tests.python-zeep.org/tns"
                 xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
                 xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                 targetNamespace="http://tests.python-zeep.org/tns">
      <types>
        <xsd:schema targetNamespace="http://tests.python-zeep.org/tns">
          <xsd:element name="Request" type="xsd:string"/>
          <xsd:element name="RequestHeader" type="xsd:string"/>
          <xsd:element name="Response" type="xsd:string"/>
          <xsd:element name="ResponseHeader" type="xsd:string"/>
        </xsd:schema>
      </types>

      <message name="Input">
        <part element="tns:Request"/>
        <part name="auth" element="tns:RequestHeader"/>
      </message>
      <message name="Output">
        <part element="tns:Response"/>
        <part name="auth" element="tns:ResponseHeader"/>
      </message>

      <portType name="TestPortType">
        <operation name="TestOperation">
          <input message="Input"/>
          <output message="Output"/>
        </operation>
      </portType>

      <binding name="TestBinding" type="tns:TestPortType">
        <soap:binding style="document" transport="http://schemas.xmlsoap.org/soap/http"/>
        <operation name="TestOperation">
          <soap:operation soapAction=""/>
          <input>
            <soap:header message="tns:Input" part="auth" use="literal" />
            <soap:body use="literal"/>
          </input>
          <output>
            <soap:header message="tns:Output" part="auth" use="literal" />
            <soap:body use="literal"/>
          </output>
        </operation>
      </binding>
    </definitions>
    """.strip())

    root = wsdl.Document(wsdl_content, None)

    binding = root.bindings['{http://tests.python-zeep.org/tns}TestBinding']
    operation = binding.get('TestOperation')

    assert operation.input.body.signature() == 'xsd:string'
    assert operation.input.header.signature() == 'auth: RequestHeader()'
    assert operation.input.envelope.signature() == 'body: xsd:string, header: {auth: RequestHeader()}'
    assert operation.input.signature(as_output=False) == 'xsd:string, _soapheaders={auth: RequestHeader()}'

    assert operation.output.body.signature() == 'xsd:string'
    assert operation.output.header.signature() == 'auth: ResponseHeader()'
    assert operation.output.envelope.signature() == 'body: xsd:string, header: {auth: ResponseHeader()}'
    assert operation.output.signature(as_output=True) == 'body: xsd:string, header: {auth: ResponseHeader()}'


def test_parse_with_header_other_message():
    wsdl_content = StringIO("""
    <definitions xmlns="http://schemas.xmlsoap.org/wsdl/"
                 xmlns:tns="http://tests.python-zeep.org/tns"
                 xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
                 xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                 targetNamespace="http://tests.python-zeep.org/tns">
      <types>
        <xsd:schema targetNamespace="http://tests.python-zeep.org/tns">
          <xsd:element name="Request" type="xsd:string"/>
          <xsd:element name="RequestHeader" type="xsd:string"/>
        </xsd:schema>
      </types>

      <message name="InputHeader">
        <part name="header" element="tns:RequestHeader"/>
      </message>
      <message name="Input">
        <part element="tns:Request"/>
      </message>

      <portType name="TestPortType">
        <operation name="TestOperation">
          <input message="Input"/>
        </operation>
      </portType>

      <binding name="TestBinding" type="tns:TestPortType">
        <soap:binding style="document" transport="http://schemas.xmlsoap.org/soap/http"/>
        <operation name="TestOperation">
          <soap:operation soapAction=""/>
          <input>
            <soap:header message="tns:InputHeader" part="header" use="literal" />
            <soap:body use="literal"/>
          </input>
        </operation>
      </binding>
    </definitions>
    """.strip())

    root = wsdl.Document(wsdl_content, None)

    binding = root.bindings['{http://tests.python-zeep.org/tns}TestBinding']
    operation = binding.get('TestOperation')

    assert operation.input.header.signature() == 'header: RequestHeader()'
    assert operation.input.body.signature() == 'xsd:string'

    header = root.types.get_element(
        '{http://tests.python-zeep.org/tns}RequestHeader'
    )('foo')
    serialized = operation.input.serialize(
        'ah1', _soapheaders={'header': header})
    expected = """
        <?xml version="1.0"?>
        <soap-env:Envelope
            xmlns:ns0="http://tests.python-zeep.org/tns"
            xmlns:soap-env="http://schemas.xmlsoap.org/soap/envelope/">
          <soap-env:Header>
            <ns0:RequestHeader>foo</ns0:RequestHeader>
          </soap-env:Header>
          <soap-env:Body>
            <ns0:Request>ah1</ns0:Request>
          </soap-env:Body>
        </soap-env:Envelope>
    """
    assert_nodes_equal(expected, serialized.content)


def test_serialize():
    wsdl_content = StringIO("""
    <definitions xmlns="http://schemas.xmlsoap.org/wsdl/"
                 xmlns:tns="http://tests.python-zeep.org/tns"
                 xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
                 xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                 targetNamespace="http://tests.python-zeep.org/tns">
      <types>
        <xsd:schema targetNamespace="http://tests.python-zeep.org/tns"
                    elementFormDefault="qualified">
          <xsd:element name="Request">
            <xsd:complexType>
              <xsd:sequence>
                <xsd:element name="arg1" type="xsd:string"/>
                <xsd:element name="arg2" type="xsd:string"/>
              </xsd:sequence>
            </xsd:complexType>
          </xsd:element>
        </xsd:schema>
      </types>

      <message name="Input">
        <part element="tns:Request"/>
      </message>

      <portType name="TestPortType">
        <operation name="TestOperation">
          <input message="Input"/>
        </operation>
      </portType>

      <binding name="TestBinding" type="tns:TestPortType">
        <soap:binding style="document" transport="http://schemas.xmlsoap.org/soap/http"/>
        <operation name="TestOperation">
          <soap:operation soapAction=""/>
          <input>
            <soap:body use="literal"/>
          </input>
        </operation>
      </binding>
    </definitions>
    """.strip())

    root = wsdl.Document(wsdl_content, None)

    binding = root.bindings['{http://tests.python-zeep.org/tns}TestBinding']
    operation = binding.get('TestOperation')

    serialized = operation.input.serialize(arg1='ah1', arg2='ah2')
    expected = """
        <?xml version="1.0"?>
        <soap-env:Envelope
            xmlns:ns0="http://tests.python-zeep.org/tns"
            xmlns:soap-env="http://schemas.xmlsoap.org/soap/envelope/">
          <soap-env:Body>
            <ns0:Request>
              <ns0:arg1>ah1</ns0:arg1>
              <ns0:arg2>ah2</ns0:arg2>
            </ns0:Request>
          </soap-env:Body>
        </soap-env:Envelope>
    """
    assert_nodes_equal(expected, serialized.content)


def test_serialize_with_header():
    wsdl_content = StringIO("""
    <definitions xmlns="http://schemas.xmlsoap.org/wsdl/"
                 xmlns:tns="http://tests.python-zeep.org/tns"
                 xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
                 xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                 targetNamespace="http://tests.python-zeep.org/tns">
      <types>
        <xsd:schema targetNamespace="http://tests.python-zeep.org/tns"
                    elementFormDefault="qualified">
          <xsd:element name="Request">
            <xsd:complexType>
              <xsd:sequence>
                <xsd:element name="arg1" type="xsd:string"/>
                <xsd:element name="arg2" type="xsd:string"/>
              </xsd:sequence>
            </xsd:complexType>
          </xsd:element>
          <xsd:element name="Authentication">
            <xsd:complexType>
              <xsd:sequence>
                <xsd:element name="username" type="xsd:string"/>
              </xsd:sequence>
            </xsd:complexType>
          </xsd:element>
        </xsd:schema>
      </types>

      <message name="Input">
        <part element="tns:Request"/>
        <part element="tns:Authentication" name="auth"/>
      </message>

      <portType name="TestPortType">
        <operation name="TestOperation">
          <input message="Input"/>
        </operation>
      </portType>

      <binding name="TestBinding" type="tns:TestPortType">
        <soap:binding style="document" transport="http://schemas.xmlsoap.org/soap/http"/>
        <operation name="TestOperation">
          <soap:operation soapAction=""/>
          <input>
            <soap:body use="literal"/>
            <soap:header message="tns:Input" part="auth" use="literal"/>
          </input>
        </operation>
      </binding>
    </definitions>
    """.strip())

    root = wsdl.Document(wsdl_content, None)

    binding = root.bindings['{http://tests.python-zeep.org/tns}TestBinding']
    operation = binding.get('TestOperation')

    AuthHeader = root.types.get_element('{http://tests.python-zeep.org/tns}Authentication')
    auth_header = AuthHeader(username='mvantellingen')

    serialized = operation.input.serialize(
        arg1='ah1', arg2='ah2', _soapheaders=[auth_header])
    serialized = operation.input.serialize(
        arg1='ah1', arg2='ah2', _soapheaders=[auth_header])
    expected = """
        <?xml version="1.0"?>
        <soap-env:Envelope
            xmlns:ns0="http://tests.python-zeep.org/tns"
            xmlns:soap-env="http://schemas.xmlsoap.org/soap/envelope/">
          <soap-env:Header>
            <ns0:Authentication>
              <ns0:username>mvantellingen</ns0:username>
            </ns0:Authentication>
          </soap-env:Header>
          <soap-env:Body>
            <ns0:Request>
              <ns0:arg1>ah1</ns0:arg1>
              <ns0:arg2>ah2</ns0:arg2>
            </ns0:Request>
          </soap-env:Body>
        </soap-env:Envelope>
    """
    assert_nodes_equal(expected, serialized.content)


def test_serialize_with_headers_simple():
    wsdl_content = StringIO("""
    <definitions xmlns="http://schemas.xmlsoap.org/wsdl/"
                 xmlns:tns="http://tests.python-zeep.org/tns"
                 xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
                 xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                 targetNamespace="http://tests.python-zeep.org/tns">
      <types>
        <xsd:schema targetNamespace="http://tests.python-zeep.org/tns"
                    elementFormDefault="qualified">
          <xsd:element name="Request">
            <xsd:complexType>
              <xsd:sequence>
                <xsd:element name="arg1" type="xsd:string"/>
                <xsd:element name="arg2" type="xsd:string"/>
              </xsd:sequence>
            </xsd:complexType>
          </xsd:element>
          <xsd:element name="Authentication">
            <xsd:complexType>
              <xsd:sequence>
                <xsd:element name="username" type="xsd:string"/>
              </xsd:sequence>
            </xsd:complexType>
          </xsd:element>
        </xsd:schema>
      </types>

      <message name="Input">
        <part element="tns:Request"/>
        <part element="tns:Authentication" name="Header"/>
      </message>

      <portType name="TestPortType">
        <operation name="TestOperation">
          <input message="Input"/>
        </operation>
      </portType>

      <binding name="TestBinding" type="tns:TestPortType">
        <soap:binding style="document" transport="http://schemas.xmlsoap.org/soap/http"/>
        <operation name="TestOperation">
          <soap:operation soapAction=""/>
          <input>
            <soap:body use="literal"/>
            <soap:header message="tns:Input" part="Header" use="literal"/>
          </input>
        </operation>
      </binding>
    </definitions>
    """.strip())

    root = wsdl.Document(wsdl_content, None)

    binding = root.bindings['{http://tests.python-zeep.org/tns}TestBinding']
    operation = binding.get('TestOperation')

    header = xsd.Element(None, xsd.ComplexType(
        xsd.Sequence([
            xsd.Element('{http://www.w3.org/2005/08/addressing}Action', xsd.String()),
            xsd.Element('{http://www.w3.org/2005/08/addressing}To', xsd.String()),
        ])
    ))
    header_value = header(Action='doehet', To='server')
    serialized = operation.input.serialize(
        arg1='ah1', arg2='ah2',
        _soapheaders=[header_value])
    expected = """
        <?xml version="1.0"?>
        <soap-env:Envelope
            xmlns:ns0="http://tests.python-zeep.org/tns"
            xmlns:soap-env="http://schemas.xmlsoap.org/soap/envelope/">
          <soap-env:Header>
            <ns1:Action xmlns:ns1="http://www.w3.org/2005/08/addressing">doehet</ns1:Action>
            <ns2:To xmlns:ns2="http://www.w3.org/2005/08/addressing">server</ns2:To>
          </soap-env:Header>
          <soap-env:Body>
            <ns0:Request>
              <ns0:arg1>ah1</ns0:arg1>
              <ns0:arg2>ah2</ns0:arg2>
            </ns0:Request>
          </soap-env:Body>
        </soap-env:Envelope>
    """
    assert_nodes_equal(expected, serialized.content)


def test_serialize_with_header_and_custom_mixed():
    wsdl_content = StringIO("""
    <definitions xmlns="http://schemas.xmlsoap.org/wsdl/"
                 xmlns:tns="http://tests.python-zeep.org/tns"
                 xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
                 xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                 targetNamespace="http://tests.python-zeep.org/tns">
      <types>
        <xsd:schema targetNamespace="http://tests.python-zeep.org/tns"
                    elementFormDefault="qualified">
          <xsd:element name="Request">
            <xsd:complexType>
              <xsd:sequence>
                <xsd:element name="arg1" type="xsd:string"/>
                <xsd:element name="arg2" type="xsd:string"/>
              </xsd:sequence>
            </xsd:complexType>
          </xsd:element>
          <xsd:element name="Authentication">
            <xsd:complexType>
              <xsd:sequence>
                <xsd:element name="username" type="xsd:string"/>
              </xsd:sequence>
            </xsd:complexType>
          </xsd:element>
        </xsd:schema>
      </types>

      <message name="Input">
        <part element="tns:Request"/>
        <part element="tns:Authentication" name="Header"/>
      </message>

      <portType name="TestPortType">
        <operation name="TestOperation">
          <input message="Input"/>
        </operation>
      </portType>

      <binding name="TestBinding" type="tns:TestPortType">
        <soap:binding style="document" transport="http://schemas.xmlsoap.org/soap/http"/>
        <operation name="TestOperation">
          <soap:operation soapAction=""/>
          <input>
            <soap:body use="literal"/>
            <soap:header message="tns:Input" part="Header" use="literal"/>
          </input>
        </operation>
      </binding>
    </definitions>
    """.strip())

    root = wsdl.Document(wsdl_content, None)

    binding = root.bindings['{http://tests.python-zeep.org/tns}TestBinding']
    operation = binding.get('TestOperation')

    header = root.types.get_element(
        '{http://tests.python-zeep.org/tns}Authentication'
    )
    header_1 = header(username='mvantellingen')

    header = xsd.Element(
        '{http://test.python-zeep.org/custom}custom',
        xsd.ComplexType([
            xsd.Element('{http://test.python-zeep.org/custom}foo', xsd.String()),
        ])
    )
    header_2 = header(foo='bar')

    serialized = operation.input.serialize(
        arg1='ah1', arg2='ah2',
        _soapheaders=[header_1, header_2])
    expected = """
        <?xml version="1.0"?>
        <soap-env:Envelope
            xmlns:ns0="http://tests.python-zeep.org/tns"
            xmlns:soap-env="http://schemas.xmlsoap.org/soap/envelope/">
          <soap-env:Header>
            <ns0:Authentication>
              <ns0:username>mvantellingen</ns0:username>
            </ns0:Authentication>
            <ns1:custom xmlns:ns1="http://test.python-zeep.org/custom">
              <ns1:foo>bar</ns1:foo>
            </ns1:custom>
          </soap-env:Header>
          <soap-env:Body>
            <ns0:Request>
              <ns0:arg1>ah1</ns0:arg1>
              <ns0:arg2>ah2</ns0:arg2>
            </ns0:Request>
          </soap-env:Body>
        </soap-env:Envelope>
    """
    assert_nodes_equal(expected, serialized.content)


def test_serializer_with_header_custom_elm():
    wsdl_content = StringIO("""
    <definitions xmlns="http://schemas.xmlsoap.org/wsdl/"
                 xmlns:tns="http://tests.python-zeep.org/tns"
                 xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
                 xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                 targetNamespace="http://tests.python-zeep.org/tns">
      <types>
        <xsd:schema targetNamespace="http://tests.python-zeep.org/tns"
                    elementFormDefault="qualified">
          <xsd:element name="Request">
            <xsd:complexType>
              <xsd:sequence>
                <xsd:element name="arg1" type="xsd:string"/>
                <xsd:element name="arg2" type="xsd:string"/>
              </xsd:sequence>
            </xsd:complexType>
          </xsd:element>
        </xsd:schema>
      </types>

      <message name="Input">
        <part element="tns:Request"/>
      </message>

      <portType name="TestPortType">
        <operation name="TestOperation">
          <input message="Input"/>
        </operation>
      </portType>

      <binding name="TestBinding" type="tns:TestPortType">
        <soap:binding style="document" transport="http://schemas.xmlsoap.org/soap/http"/>
        <operation name="TestOperation">
          <soap:operation soapAction=""/>
          <input>
            <soap:body use="literal"/>
          </input>
        </operation>
      </binding>
    </definitions>
    """.strip())

    root = wsdl.Document(wsdl_content, None)

    binding = root.bindings['{http://tests.python-zeep.org/tns}TestBinding']
    operation = binding.get('TestOperation')

    header = xsd.Element(
        '{http://test.python-zeep.org/custom}auth',
        xsd.ComplexType([
            xsd.Element('{http://test.python-zeep.org/custom}username', xsd.String()),
        ])
    )

    serialized = operation.input.serialize(
        arg1='ah1', arg2='ah2', _soapheaders=[header(username='mvantellingen')])

    expected = """
        <?xml version="1.0"?>
        <soap-env:Envelope
            xmlns:ns0="http://tests.python-zeep.org/tns"
            xmlns:soap-env="http://schemas.xmlsoap.org/soap/envelope/">
          <soap-env:Header>
            <ns1:auth xmlns:ns1="http://test.python-zeep.org/custom">
              <ns1:username>mvantellingen</ns1:username>
            </ns1:auth>
          </soap-env:Header>
          <soap-env:Body>
            <ns0:Request>
              <ns0:arg1>ah1</ns0:arg1>
              <ns0:arg2>ah2</ns0:arg2>
            </ns0:Request>
          </soap-env:Body>
        </soap-env:Envelope>
    """
    assert_nodes_equal(expected, serialized.content)


def test_serializer_with_header_custom_xml():
    wsdl_content = StringIO("""
    <definitions xmlns="http://schemas.xmlsoap.org/wsdl/"
                 xmlns:tns="http://tests.python-zeep.org/tns"
                 xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
                 xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                 targetNamespace="http://tests.python-zeep.org/tns">
      <types>
        <xsd:schema targetNamespace="http://tests.python-zeep.org/tns"
                    elementFormDefault="qualified">
          <xsd:element name="Request">
            <xsd:complexType>
              <xsd:sequence>
                <xsd:element name="arg1" type="xsd:string"/>
                <xsd:element name="arg2" type="xsd:string"/>
              </xsd:sequence>
            </xsd:complexType>
          </xsd:element>
        </xsd:schema>
      </types>

      <message name="Input">
        <part element="tns:Request"/>
      </message>

      <portType name="TestPortType">
        <operation name="TestOperation">
          <input message="Input"/>
        </operation>
      </portType>

      <binding name="TestBinding" type="tns:TestPortType">
        <soap:binding style="document" transport="http://schemas.xmlsoap.org/soap/http"/>
        <operation name="TestOperation">
          <soap:operation soapAction=""/>
          <input>
            <soap:body use="literal"/>
          </input>
        </operation>
      </binding>
    </definitions>
    """.strip())

    root = wsdl.Document(wsdl_content, None)

    binding = root.bindings['{http://tests.python-zeep.org/tns}TestBinding']
    operation = binding.get('TestOperation')

    header_value = etree.Element('{http://test.python-zeep.org/custom}auth')
    etree.SubElement(
        header_value, '{http://test.python-zeep.org/custom}username'
    ).text = 'mvantellingen'

    serialized = operation.input.serialize(
        arg1='ah1', arg2='ah2', _soapheaders=[header_value])

    expected = """
        <?xml version="1.0"?>
        <soap-env:Envelope
            xmlns:ns0="http://tests.python-zeep.org/tns"
            xmlns:soap-env="http://schemas.xmlsoap.org/soap/envelope/">
          <soap-env:Header>
            <ns0:auth xmlns:ns0="http://test.python-zeep.org/custom">
              <ns0:username>mvantellingen</ns0:username>
            </ns0:auth>
          </soap-env:Header>
          <soap-env:Body>
            <ns0:Request>
              <ns0:arg1>ah1</ns0:arg1>
              <ns0:arg2>ah2</ns0:arg2>
            </ns0:Request>
          </soap-env:Body>
        </soap-env:Envelope>
    """
    assert_nodes_equal(expected, serialized.content)


def test_deserialize():
    wsdl_content = StringIO("""
    <definitions xmlns="http://schemas.xmlsoap.org/wsdl/"
                 xmlns:tns="http://tests.python-zeep.org/tns"
                 xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
                 xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                 targetNamespace="http://tests.python-zeep.org/tns">
      <types>
        <xsd:schema targetNamespace="http://tests.python-zeep.org/tns"
                    elementFormDefault="qualified">
          <xsd:element name="Request">
            <xsd:complexType>
              <xsd:sequence>
                <xsd:element name="arg1" type="xsd:string"/>
                <xsd:element name="arg2" type="xsd:string"/>
              </xsd:sequence>
            </xsd:complexType>
          </xsd:element>
        </xsd:schema>
      </types>

      <message name="Input">
        <part element="tns:Request"/>
      </message>
      <message name="Output">
        <part element="tns:Request"/>
      </message>

      <portType name="TestPortType">
        <operation name="TestOperation">
          <input message="Input"/>
          <output message="Output"/>
        </operation>
      </portType>

      <binding name="TestBinding" type="tns:TestPortType">
        <soap:binding style="document" transport="http://schemas.xmlsoap.org/soap/http"/>
        <operation name="TestOperation">
          <soap:operation soapAction=""/>
          <input>
            <soap:body use="literal"/>
          </input>
          <output>
            <soap:body use="literal"/>
          </output>
        </operation>
      </binding>
    </definitions>
    """.strip())

    root = wsdl.Document(wsdl_content, None)

    binding = root.bindings['{http://tests.python-zeep.org/tns}TestBinding']
    operation = binding.get('TestOperation')

    response_body = load_xml("""
        <?xml version="1.0"?>
        <soap-env:Envelope
            xmlns:ns0="http://tests.python-zeep.org/tns"
            xmlns:soap-env="http://schemas.xmlsoap.org/soap/envelope/">
          <soap-env:Body>
            <ns0:Request>
              <ns0:arg1>ah1</ns0:arg1>
              <ns0:arg2>ah2</ns0:arg2>
            </ns0:Request>
          </soap-env:Body>
        </soap-env:Envelope>
    """)
    result = operation.process_reply(response_body)
    assert result.arg1 == 'ah1'
    assert result.arg2 == 'ah2'


def test_deserialize_choice():
    wsdl_content = StringIO("""
    <definitions xmlns="http://schemas.xmlsoap.org/wsdl/"
                 xmlns:tns="http://tests.python-zeep.org/tns"
                 xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
                 xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                 targetNamespace="http://tests.python-zeep.org/tns">
      <types>
        <xsd:schema targetNamespace="http://tests.python-zeep.org/tns"
                    elementFormDefault="qualified">
          <xsd:element name="Request">
            <xsd:complexType>
              <xsd:choice>
                <xsd:element name="arg1" type="xsd:string"/>
                <xsd:element name="arg2" type="xsd:string"/>
              </xsd:choice>
            </xsd:complexType>
          </xsd:element>
        </xsd:schema>
      </types>

      <message name="Input">
        <part element="tns:Request"/>
      </message>
      <message name="Output">
        <part element="tns:Request"/>
      </message>

      <portType name="TestPortType">
        <operation name="TestOperation">
          <input message="Input"/>
          <output message="Output"/>
        </operation>
      </portType>

      <binding name="TestBinding" type="tns:TestPortType">
        <soap:binding style="document" transport="http://schemas.xmlsoap.org/soap/http"/>
        <operation name="TestOperation">
          <soap:operation soapAction=""/>
          <input>
            <soap:body use="literal"/>
          </input>
          <output>
            <soap:body use="literal"/>
          </output>
        </operation>
      </binding>
    </definitions>
    """.strip())

    root = wsdl.Document(wsdl_content, None)

    binding = root.bindings['{http://tests.python-zeep.org/tns}TestBinding']
    operation = binding.get('TestOperation')

    response_body = load_xml("""
        <?xml version="1.0"?>
        <soap-env:Envelope
            xmlns:ns0="http://tests.python-zeep.org/tns"
            xmlns:soap-env="http://schemas.xmlsoap.org/soap/envelope/">
          <soap-env:Body>
            <ns0:Request>
              <ns0:arg1>ah1</ns0:arg1>
            </ns0:Request>
          </soap-env:Body>
        </soap-env:Envelope>
    """)
    result = operation.process_reply(response_body)
    assert result.arg1 == 'ah1'


def test_deserialize_one_part():
    wsdl_content = StringIO("""
    <definitions xmlns="http://schemas.xmlsoap.org/wsdl/"
                 xmlns:tns="http://tests.python-zeep.org/tns"
                 xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
                 xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                 targetNamespace="http://tests.python-zeep.org/tns">
      <types>
        <xsd:schema targetNamespace="http://tests.python-zeep.org/tns"
                    elementFormDefault="qualified">
          <xsd:element name="Request">
            <xsd:complexType>
              <xsd:sequence>
                <xsd:element name="arg1" type="xsd:string"/>
                <xsd:element name="arg2" type="xsd:string"/>
              </xsd:sequence>
            </xsd:complexType>
          </xsd:element>
        </xsd:schema>
      </types>

      <message name="Input">
        <part element="tns:Request"/>
      </message>

      <message name="Output">
        <part element="tns:Request"/>
      </message>

      <portType name="TestPortType">
        <operation name="TestOperation">
          <input message="Input"/>
          <output message="Output"/>
        </operation>
      </portType>

      <binding name="TestBinding" type="tns:TestPortType">
        <soap:binding style="document" transport="http://schemas.xmlsoap.org/soap/http"/>
        <operation name="TestOperation">
          <soap:operation soapAction=""/>
          <input>
            <soap:body use="literal"/>
          </input>
          <output>
            <soap:body use="literal"/>
          </output>
        </operation>
      </binding>
    </definitions>
    """.strip())

    root = wsdl.Document(wsdl_content, None)

    binding = root.bindings['{http://tests.python-zeep.org/tns}TestBinding']
    operation = binding.get('TestOperation')

    response_body = load_xml("""
        <?xml version="1.0"?>
        <soap-env:Envelope
            xmlns:ns0="http://tests.python-zeep.org/tns"
            xmlns:soap-env="http://schemas.xmlsoap.org/soap/envelope/">
          <soap-env:Header>
            <ns0:auth xmlns:ns0="http://test.python-zeep.org/custom">
              <ns0:username>mvantellingen</ns0:username>
            </ns0:auth>
          </soap-env:Header>
          <soap-env:Body>
            <ns0:Request>
              <ns0:arg1>ah1</ns0:arg1>
              <ns0:arg2>ah2</ns0:arg2>
            </ns0:Request>
          </soap-env:Body>
        </soap-env:Envelope>
    """)  # noqa

    serialized = operation.process_reply(response_body)
    assert serialized.arg1 == 'ah1'
    assert serialized.arg2 == 'ah2'


def test_deserialize_with_headers():
    wsdl_content = StringIO("""
    <definitions xmlns="http://schemas.xmlsoap.org/wsdl/"
                 xmlns:tns="http://tests.python-zeep.org/tns"
                 xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
                 xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                 targetNamespace="http://tests.python-zeep.org/tns">
      <types>
        <xsd:schema targetNamespace="http://tests.python-zeep.org/tns"
                    elementFormDefault="qualified">
          <xsd:element name="Request1">
            <xsd:complexType>
              <xsd:sequence>
                <xsd:element name="arg1" type="xsd:string"/>
              </xsd:sequence>
            </xsd:complexType>
          </xsd:element>

          <xsd:element name="Request2">
            <xsd:complexType>
              <xsd:sequence>
                <xsd:element name="arg2" type="xsd:string"/>
              </xsd:sequence>
            </xsd:complexType>
          </xsd:element>

          <xsd:element name="Header1">
            <xsd:complexType>
              <xsd:sequence>
                <xsd:element name="username" type="xsd:string"/>
              </xsd:sequence>
            </xsd:complexType>
          </xsd:element>
          <xsd:element name="Header2" type="xsd:string"/>
        </xsd:schema>
      </types>

      <message name="Input">
        <part element="tns:Request1"/>
      </message>

      <message name="Output">
        <part element="tns:Request1" name="request_1"/>
        <part element="tns:Request2" name="request_2"/>
        <part element="tns:Header1" name="header_1"/>
        <part element="tns:Header2" name="header_2"/>
      </message>

      <portType name="TestPortType">
        <operation name="TestOperation">
          <input message="Input"/>
          <output message="Output"/>
        </operation>
      </portType>

      <binding name="TestBinding" type="tns:TestPortType">
        <soap:binding style="document" transport="http://schemas.xmlsoap.org/soap/http"/>
        <operation name="TestOperation">
          <soap:operation soapAction=""/>
          <input>
            <soap:body use="literal"/>
          </input>
          <output>
            <soap:body use="literal"/>
            <soap:header message="tns:Output" part="header_1" use="literal">
              <soap:headerfault message="tns:OutputFault"
                    part="header_1_fault" use="literal"/>
            </soap:header>
            <soap:header message="tns:Output" part="header_2" use="literal"/>
          </output>
        </operation>
      </binding>
    </definitions>
    """.strip())

    root = wsdl.Document(wsdl_content, None)

    binding = root.bindings['{http://tests.python-zeep.org/tns}TestBinding']
    operation = binding.get('TestOperation')

    response_body = load_xml("""
        <?xml version="1.0"?>
        <soap-env:Envelope
            xmlns:ns0="http://tests.python-zeep.org/tns"
            xmlns:soap-env="http://schemas.xmlsoap.org/soap/envelope/">
          <soap-env:Header>
            <ns0:Header1>
              <ns0:username>mvantellingen</ns0:username>
            </ns0:Header1>
            <ns0:Header2>foo</ns0:Header2>
          </soap-env:Header>
          <soap-env:Body>
            <ns0:Request1>
              <ns0:arg1>ah1</ns0:arg1>
            </ns0:Request1>
            <ns0:Request2>
              <ns0:arg2>ah2</ns0:arg2>
            </ns0:Request2>
          </soap-env:Body>
        </soap-env:Envelope>
    """)  # noqa

    serialized = operation.process_reply(response_body)

    assert operation.output.signature(as_output=True) == (
        'body: {request_1: Request1(), request_2: Request2()}, header: {header_1: Header1(), header_2: Header2()}')
    assert serialized.body.request_1.arg1 == 'ah1'
    assert serialized.body.request_2.arg2 == 'ah2'
    assert serialized.header.header_1.username == 'mvantellingen'
