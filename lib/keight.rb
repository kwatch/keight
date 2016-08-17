# -*- coding: utf-8 -*-

###
### $Release: 0.0.0 $
### $Copyright: copyright(c) 2014-2016 kuwata-lab.com all rights reserved $
### $License: MIT License $
###

require 'json'
require 'date'
require 'uri'
require 'digest/sha1'
#require 'stringio'     # on-demand load


module K8

  RELEASE  = '$Release: 0.0.0 $'.split()[1]

  FILEPATH = __FILE__

  HTTP_REQUEST_METHODS = {
    "GET"     => :GET,
    "POST"    => :POST,
    "PUT"     => :PUT,
    "DELETE"  => :DELETE,
    "HEAD"    => :HEAD,
    "PATCH"   => :PATCH,
    "OPTIONS" => :OPTIONS,
    "TRACE"   => :TRACE,
  }

  ## ref: https://en.wikipedia.org/wiki/List_of_HTTP_status_codes
  HTTP_RESPONSE_STATUS = {
    100 => "Continue",
    101 => "Switching Protocols",
    102 => "Processing",                           # WebDAV; RFC 2518
    103 => "Checkpoint",                           # Unofficial
    200 => "OK",
    201 => "Created",
    202 => "Accepted",
    203 => "Non-Authoritative Information",        # since HTTP/1.1
    204 => "No Content",
    205 => "Reset Content",
    206 => "Partial Content",                      # RFC 7233
    207 => "Multi-Status",                         # WebDAV; RFC 4918
    208 => "Already Reported",                     # WebDAV; RFC 5842
    226 => "IM Used",                              # RFC 3229
    300 => "Multiple Choices",
    301 => "Moved Permanently",
    302 => "Found",
    303 => "See Other",                            # since HTTP/1.1
    304 => "Not Modified",                         # RFC 7232
    305 => "Use Proxy",                            # since HTTP/1.1
    306 => "Switch Proxy",
    307 => "Temporary Redirect",                   # since HTTP/1.1
    308 => "Permanent Redirect",                   # RFC 7538
    400 => "Bad Request",
    401 => "Unauthorized",                         # RFC 7235
    402 => "Payment Required",
    403 => "Forbidden",
    404 => "Not Found",
    405 => "Method Not Allowed",
    406 => "Not Acceptable",
    407 => "Proxy Authentication Required",        # RFC 7235
    408 => "Request Timeout",
    409 => "Conflict",
    410 => "Gone",
    411 => "Length Required",
    412 => "Precondition Failed",                  # RFC 7232
    413 => "Payload Too Large",                    # RFC 7231
    414 => "URI Too Long",                         # RFC 7231
    415 => "Unsupported Media Type",
    416 => "Range Not Satisfiable",                # RFC 7233
    417 => "Expectation Failed",
    418 => "I'm a teapot",                         # RFC 2324
   #420 => "Enhance Your Calm",                    # Twitter
   #420 => "Method Failure",                       # Spring Framework
    421 => "Misdirected Request",                  # RFC 7540
    422 => "Unprocessable Entity",                 # WebDAV; RFC 4918
    423 => "Locked",                               # WebDAV; RFC 4918
    424 => "Failed Dependency",                    # WebDAV; RFC 4918
    426 => "Upgrade Required",
    428 => "Precondition Required",                # RFC 6585
    429 => "Too Many Requests",                    # RFC 6585
    431 => "Request Header Fields Too Large",      # RFC 6585
   #440 => "Login Timeout",                        # IIS
    444 => "No Response",                          # nginx
   #449 => "Retry With",                           # IIS
   #450 => "Blocked by Windows Parental Controls", # Microsoft
   #451 => "Redirect",                             # IIS
    451 => "Unavailable For Legal Reasons",
    495 => "SSL Certificate Error",                # nginx
    496 => "SSL Certificate Required",             # nginx
    497 => "HTTP Request Sent to HTTPS Port",      # nginx
   #498 => "Invalid Token",                        # Esri
    499 => "Client Closed Request",                # nginx
   #499 => "Request has been forbidden by antivirus",
   #499 => "Token Required",                       # Esri
    500 => "Internal Server Error",
    501 => "Not Implemented",
    502 => "Bad Gateway",
    503 => "Service Unavailable",
    504 => "Gateway Timeout",
    505 => "HTTP Version Not Supported",
    506 => "Variant Also Negotiates",              # RFC 2295
    507 => "Insufficient Storage",                 # WebDAV; RFC 4918
    508 => "Loop Detected",                        # WebDAV; RFC 5842
    509 => "Bandwidth Limit Exceeded",             # Apache Web Server/cPanel
    510 => "Not Extended",                         # RFC 2774
    511 => "Network Authentication Required",      # RFC 6585
    520 => "Unknown Error",                        # CloudFlare
    521 => "Web Server Is Down",                   # CloudFlare
    522 => "Connection Timed Out",                 # CloudFlare
    523 => "Origin Is Unreachable",                # CloudFlare
    524 => "A Timeout Occurred",                   # CloudFlare
    525 => "SSL Handshake Failed",                 # CloudFlare
    526 => "Invalid SSL Certificate",              # CloudFlare
   #530 => "Site is frozen",                       # Unofficial
  }.each {|_, v| v.freeze }

  MIME_TYPES = {
    '.html'    => 'text/html',
    '.htm'     => 'text/html',
    '.shtml'   => 'text/html',
    '.css'     => 'text/css',
    '.csv'     => 'text/comma-separated-values',
    '.tsv'     => 'text/tab-separated-values',
    '.xml'     => 'text/xml',
    '.mml'     => 'text/mathml',
    '.txt'     => 'text/plain',
    '.wml'     => 'text/vnd.wap.wml',
    '.gif'     => 'image/gif',
    '.jpeg'    => 'image/jpeg',
    '.jpg'     => 'image/jpeg',
    '.png'     => 'image/png',
    '.tif'     => 'image/tiff',
    '.tiff'    => 'image/tiff',
    '.ico'     => 'image/x-icon',
    '.bmp'     => 'image/x-ms-bmp',
    '.svg'     => 'image/svg+xml',
    '.svgz'    => 'image/svg+xml',
    '.webp'    => 'image/webp',
    '.mid'     => 'audio/midi',
    '.midi'    => 'audio/midi',
    '.kar'     => 'audio/midi',
    '.mp3'     => 'audio/mpeg',
    '.ogg'     => 'audio/ogg',
    '.m4a'     => 'audio/x-m4a',
    '.ra'      => 'audio/x-realaudio',
    '.3gpp'    => 'video/3gpp',
    '.3gp'     => 'video/3gpp',
    '.3g2'     => 'video/3gpp2',
    '.ts'      => 'video/mp2t',
    '.mp4'     => 'video/mp4',
    '.mpeg'    => 'video/mpeg',
    '.mpg'     => 'video/mpeg',
    '.mov'     => 'video/quicktime',
    '.webm'    => 'video/webm',
    '.flv'     => 'video/x-flv',
    '.m4v'     => 'video/x-m4v',
    '.mng'     => 'video/x-mng',
    '.asx'     => 'video/x-ms-asf',
    '.asf'     => 'video/x-ms-asf',
    '.wmv'     => 'video/x-ms-wmv',
    '.avi'     => 'video/x-msvideo',
    '.json'    => 'application/json',
    '.js'      => 'application/javascript',
    '.atom'    => 'application/atom+xml',
    '.rss'     => 'application/rss+xml',
    '.doc'     => 'application/msword',
    '.pdf'     => 'application/pdf',
    '.ps'      => 'application/postscript',
    '.eps'     => 'application/postscript',
    '.ai'      => 'application/postscript',
    '.rtf'     => 'application/rtf',
    '.xls'     => 'application/vnd.ms-excel',
    '.eot'     => 'application/vnd.ms-fontobject',
    '.ppt'     => 'application/vnd.ms-powerpoint',
    '.key'     => 'application/vnd.apple.keynote',
    '.pages'   => 'application/vnd.apple.pages',
    '.numbers' => 'application/vnd.apple.numbers',
    '.zip'     => 'application/zip',
    '.lha'     => 'application/x-lzh',
    '.lzh'     => 'application/x-lzh',
    '.tar'     => 'application/x-tar',
    '.tgz'     => 'application/x-tar',
    '.gz'      => 'application/x-gzip',
    '.bz2'     => 'application/x-bzip2',
    '.xz'      => 'application/x-xz',
    '.7z'      => 'application/x-7z-compressed',
    '.rar'     => 'application/x-rar-compressed',
    '.rpm'     => 'application/x-redhat-package-manager',
    '.deb'     => 'application/vnd.debian.binary-package',
    '.swf'     => 'application/x-shockwave-flash',
    '.der'     => 'application/x-x509-ca-cert',
    '.pem'     => 'application/x-x509-ca-cert',
    '.crt'     => 'application/x-x509-ca-cert',
    '.xpi'     => 'application/x-xpinstall',
    '.xhtml'   => 'application/xhtml+xml',
    '.xspf'    => 'application/xspf+xml',
    '.yaml'    => 'application/x-yaml',
    '.yml'     => 'application/x-yaml',
    '.docx'    => 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.xlsx'    => 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    '.pptx'    => 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
  }.each {|_, v| v.freeze }  # hash keys are always frozen


  module Util

    module_function

    ESCAPE_HTML = {'&'=>'&amp;', '<'=>'&lt;', '>'=>'&gt;', '"'=>'&quot;', "'"=>'&#39;'}

    def escape_html(str)
      #; [!90jx8] escapes '& < > " \'' into '&amp; &lt; &gt; &quot; &#39;'.
      return str.gsub(/[&<>"']/, ESCAPE_HTML)
    end

    #; [!649wt] 'h()' is alias of 'escape_html()'
    alias h escape_html
    class << self
      alias h escape_html
    end

    def percent_encode(str)
      #; [!a96jo] encodes string into percent encoding format.
      return URI.encode_www_form_component(str)
    end

    def percent_decode(str)
      #; [!kl9sk] decodes percent encoded string.
      return URI.decode_www_form_component(str)
    end

    def parse_query_string(query_str)
      return _parse(query_str, /[&;]/)
    end

    def parse_cookie_string(cookie_str)
      return _parse(cookie_str, /;\s*/)
    end

    def _parse(query_str, separator)
      #; [!engr6] returns empty Hash/dict object when query string is empty.
      d = {}
      return d if query_str.empty?
      #; [!fzt3w] parses query string and returns Hash/dict object.
      equal    = '='
      brackets = '[]'
      query_str.split(separator).each do |s|
        #kv = s.split('=', 2)
        #if kv.length == 2
        #  k, v = kv
        #else
        #  k = kv[0]; v = ""
        #end
        k, v = s.split(equal, 2)
        v ||= ''
        k = percent_decode(k) unless k =~ /\A[-.\w]+\z/
        v = percent_decode(v) unless v =~ /\A[-.\w]+\z/
        #; [!t0w33] regards as array of string when param name ends with '[]'.
        if k.end_with?(brackets)
          (d[k] ||= []) << v
        else
          d[k] = v
        end
      end
      return d
    end

    def build_query_string(query)
      case query
      when nil    ; return nil
      when String ; return query
      when Hash, Array
        return query.collect {|k, v| "#{percent_decode(k.to_s)}=#{percent_decode(v.to_s)}" }.join('&')
      else
        raise ArgumentError.new("Hash or Array expected but got #{query.inspect}.")
      end
    end

    MULTIPART_MAX_FILESIZE       =   50 * 1024 * 1024   #  50MB
    MULTIPART_BUFFER_SIZE        =   10 * 1024 * 1024   #  10MB

    def parse_multipart(stdin, boundary, content_length, max_filesize=nil, bufsize=nil)
      max_filesize ||= MULTIPART_MAX_FILESIZE
      bufsize      ||= MULTIPART_BUFFER_SIZE
      #; [!mqrei] parses multipart form data.
      params = {}   # {"name": "value"}
      files  = {}   # {"name": UploadedFile}
      _parse_multipart(stdin, boundary, content_length, max_filesize, bufsize) do |part|
        header, body = part.split("\r\n\r\n")
        pname, filename, cont_type = _parse_multipart_header(header)
        if filename
          upfile = UploadedFile.new(filename, cont_type) {|f| f.write(body) }
          pvalue = filename
        else
          upfile = nil
          pvalue = body
        end
        if pname.end_with?('[]')
          (params[pname] ||= []) << pvalue
          (files[pname]  ||= []) << upfile if upfile
        else
          params[pname] = pvalue
          files[pname]  = upfile if upfile
        end
      end
      return params, files
    end

    def _parse_multipart(stdin, boundary, content_length, max_filesize, bufsize)
      first_line = "--#{boundary}\r\n"
      last_line  = "\r\n--#{boundary}--\r\n"
      separator  = "\r\n--#{boundary}\r\n"
      s = stdin.read(first_line.bytesize)
      s == first_line  or
        raise _mp_err("invalid first line. exected=#{first_line.inspect}, actual=#{s.inspect}")
      len = content_length - first_line.bytesize - last_line.bytesize
      len > 0  or
        raise _mp_err("invalid content length.")
      last = nil
      while len > 0
        n = bufsize < len ? bufsize : len
        buf = stdin.read(n)
        break if buf.nil? || buf.empty?
        len -= buf.bytesize
        buf = (last << buf) if last
        parts = buf.split(separator)
        ! (parts.length == 1 && buf.bytesize > max_filesize)  or
          raise _mp_err("too large file or data (max: about #{max_filesize/(1024*1024)}MB)")
        last = parts.pop()
        parts.each do |part|
          yield part
        end
      end
      yield last if last
      s = stdin.read(last_line.bytesize)
      s == last_line  or
        raise _mp_err("invalid last line.")
    end
    private :_parse_multipart

    def _parse_multipart_header(header)
      cont_disp = cont_type = nil
      header.split("\r\n").each do |line|
        name, val = line.split(/: */, 2)
        if    name == 'Content-Disposition'; cont_disp = val
        elsif name == 'Content-Type'       ; cont_type = val
        else                               ; nil
        end
      end
      cont_disp  or
        raise _mp_err("Content-Disposition is required.")
      cont_disp =~ /form-data; *name=(?:"([^"\r\n]*)"|([^;\r\n]+))/  or
        raise _mp_err("Content-Disposition is invalid.")
      param_name = percent_decode($1 || $2)
      filename = (cont_disp =~ /; *filename=(?:"([^"\r\n]+)"|([^;\r\n]+))/ \
                  ? percent_decode($1 || $2) : nil)
      return param_name, filename, cont_type
    end
    private :_parse_multipart_header

    def _mp_err(msg)
      return HttpException.new(400, msg)
    end
    private :_mp_err

    def randstr_b64()
      #; [!yq0gv] returns random string, encoded with urlsafe base64.
      ## Don't use SecureRandom; entropy of /dev/random or /dev/urandom
      ## should be left for more secure-sensitive purpose.
      s = "#{rand()}#{rand()}#{rand()}#{Time.now.to_f}"
      binary = Digest::SHA1.digest(s)
      return [binary].pack('m').chomp("=\n").tr('+/', '-_')
    end

    def guess_content_type(filename, default='application/octet-stream')
      #; [!xw0js] returns content type guessed from filename.
      #; [!dku5c] returns 'application/octet-stream' when failed to guess content type.
      ext = File.extname(filename)
      return MIME_TYPES[ext] || default
    end

    def http_utc_time(utc_time)   # similar to Time#httpdate() in 'time.rb'
      #; [!3z5lf] raises error when argument is not UTC.
      utc_time.utc?  or
        raise ArgumentError.new("http_utc_time(#{utc_time.inspect}): expected UTC time but got local time.")
      #; [!5k50b] converts Time object into HTTP date format string.
      return utc_time.strftime('%a, %d %b %Y %H:%M:%S GMT')
    end

    WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].freeze
    MONTHS   = [nil, 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                     'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'].freeze

    t = Time.now.utc
    if t.strftime('%a') != WEEKDAYS[t.wday] || t.strftime('%b') != MONTHS[t.month]
      def http_utc_time(utc_time)
        utc_time.utc?  or
          raise ArgumentError.new("http_utc_time(#{utc_time.inspect}): expected UTC time but got local time.")
        return utc_time.strftime("#{WEEKDAYS[utc_time.wday]}, %d #{MONTHS[utc_time.month]} %Y %H:%M:%S GMT")
      end
    end


    ##
    ## Temporary file which is removed automatically at end of response.
    ##
    ## Example:
    ##
    ##     def do_download_csv()
    ##       ## generate temporary filepath
    ##       tmpfile = K8::Util::TemporaryFile.new
    ##       p tmpfile.path      #=> ex: '/var/tmp/tmp-0372042668525.tmp'
    ##       p File.exist?(tmpfile.path)   #=> false
    ##       ## create temporary file and content
    ##       sql = "select * from table1"
    ##       system("psql dbname -A -F',' -c \"#{sql}\" | gzip > #{tmpfile.path}")
    ##       p File.exist?(tmpfile.path)   #=> true
    ##       ## set resonse headers
    ##       @resp.headers['Content-Type']        = 'text/csv;charset=UTF-8'
    ##       @resp.headers['Content-Length']      = File.size(tmpfile.path)
    ##       @resp.headers['Content-Disposition'] = 'attachment;filename="file1.csv"'
    ##       @resp.headers['Content-Encoding']    = "gzip"
    ##       ## return temporary file
    ##       return tmpfile  # will be removed automatically at end of response!!
    ##     end
    ##
    class TemporaryFile

      TMPDIR     = (ENV['TMPDIR'] || proc {require 'etc'; Etc.systmpdir}.call || '/tmp').chomp('/')
      CHUNK_SIZE = 8 * 1024   # 8KB

      def self.new_path(tmpdir=nil)
        #; [!hvnzd] generates new temorary filepath under temporary directory.
        #; [!ulb2e] uses default temporary directory path if tmpdir is not specified.
        tmpdir ||= TMPDIR
        randstr = rand().to_s[2..14]
        return "#{tmpdir}/tmp-#{randstr}.tmp"
      end

      def initialize(path=nil, tmpdir: nil, chunk_size: nil)
        #; [!ljilm] generates temporary filepath automatically when filepath is not specified.
        @path       = path || self.class.new_path(tmpdir)
        @tmpdir     = tmpdir if tmpdir
        @chunk_size = chunk_size if chunk_size
      end

      attr_reader :path

      def each
        #; [!d9suq] opens temporary file with binary mode.
        #; [!68xdj] reads chunk size data from temporary file per iteration.
        size = @chunk_size || CHUNK_SIZE
        File.open(@path, 'rb') do |f|
          yield f.read(size)
        end
      ensure
        #; [!i0dmd] removes temporary file automatically at end of loop.
        #; [!347an] removes temporary file even if error raised in block.
        File.unlink @path
        self
      end

    end


    ##
    ## Invoke shell command and responses it's output to client.
    ##
    ## Example:
    ##
    ##     def do_download_csv()
    ##       sql = "select * from table1"
    ##       cmd = "psql -AF',' dbname | iconv -f UTF-8 -t CP932 -c | gzip"
    ##       shell_command = K8::Util::ShellCommand.new(cmd, input: sql)
    ##       begin
    ##         return shell_command.start() do
    ##           @resp.headers['Content-Type']        = "text/csv;charset=Shift_JIS"
    ##           @resp.headers['Content-Disposition'] = 'attachment;filename="file1.tsv"'
    ##           @resp.headers['Content-Encoding']    = "gzip"
    ##         end
    ##       rescue K8::Util::ShellCommandError => ex
    ##         @resp.status = 500
    ##         @resp.headers['Content-Type'] = "text/plain;charset=UTF-8"
    ##         return ex.message
    ##       end
    ##       command.start
    ##     end
    ##
    class ShellCommand

      CHUNK_SIZE = 8 * 1024

      def initialize(command, input: nil, chunk_size: nil, &teardown)
        #; [!j95pi] takes shell command and input string.
        @command    = command  # ex: "psql -AF',' dbname | gzip"
        @input      = input    # ex: "select * from table1"
        @chunk_size = chunk_size || CHUNK_SIZE
        @teardown   = teardown
        @pid        = nil      # process id
        @tuple      = nil
      end

      attr_reader :command, :input, :pid

      def start
        #; [!66uck] not allowed to start more than once.
        @pid.nil?  or    # TODO: close sout and serr
          raise ShellCommandError.new("Already started (comand: #{@command.inspect})")
        #; [!9seos] invokes shell command.
        require 'open3' unless defined?(Open3)
        sin, sout, serr, waiter = Open3.popen3(@command)
        @pid = waiter.pid
        size = @chunk_size
        begin
          #; [!d766y] writes input string if provided to initializer.
          sin.write(input) if input
          sin.close()
          #; [!f651x] reads first chunk data.
          #; [!cjstj] raises ShellCommandError when command prints something to stderr.
          chunk = sout.read(size)
          if chunk.nil?
            error = serr.read()
            log_error(error.to_s)
            error = "Command failed: #{@command}" if ! error || error.empty?
            raise ShellCommandError.new(error)
          end
          #; [!bt12n] saves stdout, stderr, command process, and first chunk data.
          @tuple = [sout, serr, waiter, chunk]
          #; [!kgnel] yields callback (if given) when command invoked successfully.
          yield if block_given?
        #; [!2989u] closes both stdout and stderr when error raised.
        rescue => ex
          sout.close()
          serr.close()
          raise
        end
        #; [!fp98i] returns self.
        self
      end

      def each
        #; [!ssgmm] '#start()' should be called before '#each()'.
        @pid  or
          raise ShellCommandError.new("Not started yet (command: #{@command.inspect}).")
        #; [!vpmbw] yields each chunk data.
        sout, serr, waiter, chunk = @tuple
        @tuple = nil
        yield chunk
        size = @chunk_size
        ex = nil
        begin
          while (chunk = sout.read(size))
            yield chunk
          end
          #; [!70xdy] logs stderr output.
          error = serr.read()
          log_error(error) if error && ! error.empty?
        rescue => ex
          raise
        ensure
          #; [!2wll8] closes stdout and stderr, even if error raised.
          sout.close()
          serr.close()
          #; [!0ebq5] calls callback specified to initializer with error object.
          @teardown.yield(ex) if @teardown
        end
        #; [!ln8we] returns self.
        self
      end

      def log_error(message)
        $stderr.write("[ERROR] ShellCommand: #{@command.inspect} #-------\n")
        $stderr.write(message); $stderr.write("\n") unless message.end_with?("\n")
        $stderr.write("--------------------\n")
      end

    end


    class ShellCommandError < StandardError
    end


  end


  class UploadedFile

    def initialize(filename, content_type)
      #; [!ityxj] takes filename and content type.
      @filename     = filename
      @content_type = content_type
      #; [!5c8w6] sets temporary filepath with random string.
      @tmp_filepath = new_filepath()
      #; [!8ezhr] yields with opened temporary file.
      File.open(@tmp_filepath, 'wb') {|f| yield f } if block_given?
    end

    attr_reader :filename, :content_type, :tmp_filepath

    def clean
      #; [!ft454] removes temporary file if exists.
      File.unlink(@tmp_filepath) if @tmp_filepath
    rescue SystemCallError   # or Errno::ENOENT?
      nil
    end

    protected

    def new_filepath
      #; [!zdkts] use $K8_UPLOAD_DIR environment variable as temporary directory.
      dir = ENV['K8_UPLOAD_DIR']
      dir ||= ENV['TMPDIR'] || ENV['TEMPDIR'] || '/tmp'
      return File.join(dir, "up.#{Util.randstr_b64()}")
    end

  end


  class HttpException < Exception

    def initialize(status_code, message=nil, response_headers=nil)
      response_headers, message = message, nil if message.is_a?(Hash)
      @status_code      = status_code
      @message          = message          if message
      @response_headers = response_headers if response_headers
    end

    attr_reader :status_code, :message, :response_headers

    def status_message
      return HTTP_RESPONSE_STATUS[@status_code]
    end

  end


  class BaseError < StandardError
  end


  class ActionMappingError < BaseError
  end


  class ContentTypeRequiredError < BaseError
  end


  class UnknownActionMethodError < BaseError
  end


  class UnknownContentError < BaseError
  end


  ## Equivarent to BaseController or AbstractRequestHandler in other framework.
  class BaseAction

    def initialize(req, resp)
      #; [!uotpb] accepts request and response objects.
      @req  = req
      @resp = resp
    end

    attr_reader :req, :resp, :sess

    def handle_action(action_name, urlpath_args)
      @action_name = action_name
      @action_args = urlpath_args
      ex = nil
      begin
        #; [!5jnx6] calls '#before_action()' before handling request.
        before_action()
        #; [!ddgx3] invokes action method with urlpath params.
        content = invoke_action(action_name, urlpath_args)
        #; [!aqa4e] returns content.
        return handle_content(content)
      rescue Exception => ex
        raise
      ensure
        #; [!67awf] calls '#after_action()' after handling request.
        #; [!alpka] calls '#after_action()' even when error raised.
        after_action(ex)
      end
    end

    protected

    def before_action
    end

    def after_action(ex)
    end

    def invoke_action(action_name, urlpath_args)
      return self.__send__(action_name, *urlpath_args)
    end

    def handle_content(content)
      return content
    end

    ##
    ## ex:
    ##   mapping '/',     :GET=>:do_index, :POST=>:do_create
    ##   mapping '/{id}', :GET=>:do_show, :PUT=>:do_update, :DELETE=>:do_delete
    ##
    def self.mapping(urlpath_pattern, action_methods={})
      action_methods.each do |req_meth, action_name|
        HTTP_REQUEST_METHODS[req_meth.to_s]  or
          raise ArgumentError.new("#{req_meth.inspect}: unknown request method.")
        req_meth.is_a?(Symbol)  or
          raise ArgumentError.new("#{req_meth.inspect}: should be a Symbol but got #{req_meth.class.name}")
      end
      #; [!o148k] maps urlpath pattern and request methods.
      self._mappings << [urlpath_pattern, action_methods]
      return self
    end

    def self._mappings
      return @action_method_mapping ||= []
    end

    def self._build_action_info(full_urlpath_pattern)   # :nodoc:
      #; [!ordhc] build ActionInfo objects for each action methods.
      parent = full_urlpath_pattern
      d = {}
      self._mappings.each do |urlpath_pat, action_methods|
        action_methods.each do |req_meth, action_name|
          info = ActionInfo.create(req_meth, "#{parent}#{urlpath_pat}")
          d[action_name] = info
        end
      end
      @action_infos = d
    end

    def self.[](action_name)
      #; [!1tq8z] returns ActionInfo object corresponding to action method.
      #; [!6g2iw] returns nil when not mounted yet.
      return (@action_infos || {})[action_name]
    end

  end


  ## Equivarent to Controller or RequestHandler in other framework.
  class Action < BaseAction

    #; [!siucz] request object is accessable with 'request' method as well as 'req'.
    #; [!qnzp6] response object is accessable with 'response' method as well as 'resp'.
    #; [!bd3y4] session object is accessable with 'session' method as well as 'sess'.
    alias request  req    # just for compatibility with other frameworks; use @req!
    alias response resp   # just for compatibility with other frameworks; use @resp!
    alias session  sess   # just for compatibility with other frameworks; use @sess!

    def initialize(req, res)
      super
      #; [!7sfyf] sets session object.
      @sess = req.env['rack.session']
    end

    protected

    def before_action
      csrf_protection() if csrf_protection_required?()
    end

    def after_action(ex)
      return if ex
      #; [!qsz2z] raises ContentTypeRequiredError when content type is not set.
      unless @resp.headers['Content-Type']
        status = @resp.status
        status < 200 || 300 <= status || status == 204  or
          raise ContentTypeRequiredError.new("Response header 'Content-Type' expected, but not provided.")
      end
    end

    def invoke_action(action_name, urlpath_args)
      begin
        return super
      #; [!d5v0l] handles exception when handler method defined.
      rescue => ex
        handler = "on_#{ex.class}"
        return __send__(handler, ex) if respond_to?(handler)
        raise
      end
    end

    def handle_content(content)
      case content
      #; [!jhnzu] when content is nil...
      when nil
        #; [!sfwfz] returns [''].
        return [""]
      #; [!lkxua] when content is a hash object...
      when Hash
        #; [!9aaxl] converts hash object into JSON string.
        #; [!c7nj7] sets content length.
        #; [!j0c1d] sets content type as 'application/json' when not set.
        #; [!gw05f] returns array of JSON string.
        json_str = JSON.dump(content)
        @resp.headers['Content-Length'] = json_str.bytesize.to_s
        @resp.headers['Content-Type'] ||= "application/json"
        return [json_str]
      #; [!p6p99] when content is a string...
      when String
        #; [!1ejgh] sets content length.
        #; [!uslm5] sets content type according to content when not set.
        #; [!5q1u5] raises error when failed to detect content type.
        #; [!79v6x] returns array of string.
        @resp.headers['Content-Length'] = content.bytesize.to_s
        @resp.headers['Content-Type'] ||= detect_content_type(content)  or
          raise ContentTypeRequiredError.new("Content-Type response header required.")
        return [content]
      #; [!s7eix] when content is an Enumerable object...
      when Enumerable
        #; [!md2go] just returns content.
        #; [!ab3vr] neither content length nor content type are not set.
        return content
      #; [!apwh4] else...
      else
        #; [!wmgnr] raises K8::UnknownContentError.
        raise UnknownContentError.new("Unknown content: class={content.class}, content=#{content.inspect}")
      end
    end

    ## helpers

    ## Returns "text/html; charset=utf-8" or "application/json" or nil.
    def detect_content_type(text)
      #; [!onjro] returns 'text/html; charset=utf-8' when text starts with '<'.
      #; [!qiugc] returns 'application/json' when text starts with '{'.
      #; [!zamnv] returns nil when text starts with neight '<' nor '{'.
      case text
      when /\A\s*</ ; return "text/html; charset=utf-8"  # probably HTML
      when /\A\s*\{/; return "application/json"          # probably JSON
      else          ; return nil
      end
    end

    #--
    #def HTTP(status, message=nil, response_headers=nil)
    #  return HttpException.new(status, message, response_headers)
    #end
    #++

    def redirect_to(location, status=302, flash: nil)
      #; [!xkrfk] sets flash message if provided.
      set_flash_message(flash) if flash
      #; [!ev9nu] sets response status code as 302.
      @resp.status = status
      #; [!spfge] sets Location response header.
      @resp.headers['Location'] = location
      #; [!k3gvm] returns html anchor tag.
      href = Util.h(location)
      return "<a href=\"#{href}\">#{href}</a>"
    end

    def set_flash_message(message)
      #; [!9f0iv] sets flash message into session.
      self.sess['_flash'] = message
    end

    def get_flash_message
      #; [!5minm] returns flash message stored in session.
      #; [!056bp] deletes flash message from sesson.
      return self.sess.delete('_flash')
    end

    def validation_failed
      #; [!texnd] sets response status code as 422.
      @resp.status = 422    # 422 Unprocessable Entity
      nil
    end

    ##
    ## helpers for CSRF protection
    ##

    protected

    def csrf_protection_required?
      #; [!8chgu] returns false when requested with 'XMLHttpRequest'.
      return false if @req.env['HTTP_X_REQUESTED_WITH'] == 'XMLHttpRequest'
      #; [!vwrqv] returns true when request method is one of POST, PUT, or DELETE.
      #; [!jfhla] returns true when request method is GET or HEAD.
      req_meth = @req.meth
      return req_meth == :POST || req_meth == :PUT || req_meth == :DELETE
    end

    def csrf_protection
      #; [!h5tzb] raises nothing when csrf token matched.
      #; [!h0e0q] raises HTTP 400 when csrf token mismatched.
      expected = csrf_get_token()
      actual   = csrf_get_param()
      expected == actual  or
        raise HttpException.new(400, "invalid csrf token")     # TODO: logging
      nil
    end

    def csrf_get_token
      #; [!mr6md] returns csrf cookie value.
      @req.cookies['_csrf']
    end

    def csrf_set_token(token)
      #; [!8hm2o] sets csrf cookie and returns token.
      @resp.set_cookie('_csrf', token)
      token
    end

    def csrf_get_param
      #; [!pal33] returns csrf token in request parameter.
      self.req.params['_csrf']
    end

    def csrf_new_token
      #; [!zl6cl] returns new random token.
      #; [!sfgfx] uses SHA1 + urlsafe BASE64.
      return Util.randstr_b64()
    end

    def csrf_token
      #; [!7gibo] returns current csrf token.
      #; [!6vtqd] creates new csrf token and set it to cookie when csrf token is blank.
      return @_csrf_token ||= (csrf_get_token() || csrf_set_token(csrf_new_token()))
    end

    ##

    def send_file(filepath, content_type=nil)
      #; [!iblvb] raises 404 Not Found when file not exist.
      File.file?(filepath)  or raise HttpException.new(404)
      #; [!v7r59] returns nil with status code 304 when not modified.
      mtime_utc = File.mtime(filepath).utc
      mtime_str = K8::Util.http_utc_time(mtime_utc)
      if mtime_str == @req.env['HTTP_IF_MODIFIED_SINCE']
        @resp.status = 304
        return nil
      end
      #; [!woho6] when gzipped file exists...
      content_type ||= K8::Util.guess_content_type(filepath)
      gzipped = "#{filepath}.gz"
      if File.file?(gzipped) && mtime_utc <= File.mtime(gzipped).utc
        #; [!9dmrf] returns gzipped file object when 'Accept-Encoding: gzip' exists.
        #; [!m51dk] adds 'Content-Encoding: gzip' when 'Accept-Encoding: gzip' exists.
        if /\bgzip\b/.match(@req.env['HTTP_ACCEPT_ENCODING'])
          @resp.headers['Content-Encoding'] = 'gzip'
          filepath = gzipped
        end
      end
      #; [!e8l5o] sets Content-Type with guessing it from filename.
      #; [!qhx0l] sets Content-Length with file size.
      #; [!6j4fh] sets Last-Modified with file timestamp.
      #; [!37i9c] returns opened file.
      file = File.open(filepath)
      headers = @resp.headers
      headers['Content-Type'] ||= content_type
      headers['Content-Length'] = File.size(filepath).to_s
      headers['Last-Modified']  = mtime_str
      return file
    end

  end


  ##
  ## ex:
  ##   info = ActionInfo.new('PUT', '/api/books/{id}')
  ##   p info.method                 #=> "PUT"
  ##   p info.urlpath(123)           #=> "/api/books/123"
  ##   p info.form_action_attr(123)  #=> "/api/books/123?_method=PUT"
  ##
  class ActionInfo

    def initialize(method, urlpath_format)
      @meth = method
      @urlpath_format = urlpath_format   # ex: '/books/%s/comments/%s'
    end

    attr_reader :meth

    ## (experimental; use #meth instead)
    def method(name=nil)    # :nodoc:
      return name ? super : @meth
    end

    def path(*args)
      return @urlpath_format % args
    end

    def form_action_attr(*args)
      #; [!qyhkm] returns '/api/books/123' when method is POST.
      #; [!kogyx] returns '/api/books/123?_method=PUT' when method is not POST.
      if @meth == 'POST'
        return path(*args)
      else
        return "#{path(*args)}?_method=#{@meth}"
      end
    end

    def self.create(meth, urlpath_pattern)
      ## ex: '/books/{id}' -> '/books/%s'
      #; [!1nk0i] replaces urlpath parameters with '%s'.
      #; [!a7fqv] replaces '%' with'%%'.
      rexp = /(.*?)\{(\w*?)(?::[^{}]*(?:\{[^{}]*?\}[^{}]*?)*)?\}/
      urlpath_format = ''; n = 0
      urlpath_pattern.scan(rexp) do |text, pname|
        next if pname == 'ext'   # ignore '.html' or '.json'
        urlpath_format << text.gsub(/%/, '%%') << '%s'
        n += 1
      end
      rest = n > 0 ? Regexp.last_match.post_match : urlpath_pattern
      urlpath_format << rest.gsub(/%/, '%%')
      #; [!btt2g] returns ActionInfoN object when number of urlpath parameter <= 4.
      #; [!x5yx2] returns ActionInfo object when number of urlpath parameter > 4.
      return (SUBCLASSES[n] || ActionInfo).new(meth, urlpath_format)
    end

    SUBCLASSES = []     # :nodoc:

  end

  class ActionInfo0 < ActionInfo    # :nodoc:
    def path(); @urlpath_format; end
  end

  class ActionInfo1 < ActionInfo    # :nodoc:
    def path(a); @urlpath_format % [a]; end
  end

  class ActionInfo2 < ActionInfo    # :nodoc:
    def path(a, b); @urlpath_format % [a, b]; end
  end

  class ActionInfo3 < ActionInfo    # :nodoc:
    def path(a, b, c); @urlpath_format % [a, b, c]; end
  end

  class ActionInfo4 < ActionInfo    # :nodoc:
    def path(a, b, c, d); @urlpath_format % [a, b, c, d]; end
  end

  ActionInfo::SUBCLASSES << ActionInfo0 << ActionInfo1 << ActionInfo2 << ActionInfo3 << ActionInfo4


  class DefaultPatterns

    def initialize
      @patterns = []
    end

    def register(urlpath_param_name, default_pattern='[^/]*?', &converter)
      #; [!yfsom] registers urlpath param name, default pattern and converter block.
      @patterns << [urlpath_param_name, default_pattern, converter]
      self
    end

    def unregister(urlpath_param_name)
      #; [!3gplv] deletes matched record.
      @patterns.delete_if {|tuple| tuple[0] == urlpath_param_name }
      self
    end

    def lookup(urlpath_param_name)
      #; [!dvbqx] returns default pattern string and converter proc when matched.
      #; [!6hblo] returns '[^/]+?' and nil as default pattern and converter proc when nothing matched.
      for str_or_rexp, default_pat, converter in @patterns
        return default_pat, converter if str_or_rexp === urlpath_param_name
      end
      return '[^/]+?', nil
    end

  end


  DEFAULT_PATTERNS = proc {
    x = DefaultPatterns.new
    #; [!i51id] registers '\d+' as default pattern of param 'id' or /_id\z/.
    x.register('id',    '\d+') {|val| val.to_i }
    x.register(/_id\z/, '\d+') {|val| val.to_i }
    #; [!2g08b] registers '(?:\.\w+)?' as default pattern of param 'ext'.
    x.register('ext',   '(?:\.\w+)?')
    #; [!8x5mp] registers '\d\d\d\d-\d\d-\d\d' as default pattern of param 'date' or /_date\z/.
    to_date = proc {|val|
      #; [!wg9vl] raises 404 error when invalid date (such as 2012-02-30).
      yr, mo, dy = val.split(/-/).map(&:to_i)
      Date.new(yr, mo, dy)  rescue
        raise HttpException.new(404, "#{val}: invalid date.")
    }
    x.register('date',    '\d\d\d\d-\d\d-\d\d', &to_date)
    x.register(/_date\z/, '\d\d\d\d-\d\d-\d\d', &to_date)
    x
  }.call()


  class ActionMapping

    def initialize(urlpath_mapping, urlpath_cache_size: 0,
                                    enable_urlpath_param_range: true)
      #; [!34o67] keyword arg 'enable_urlpath_param_range' controls to generate range object or not.
      @enable_urlpath_param_range = enable_urlpath_param_range
      #; [!buj0d] prepares LRU cache if cache size specified.
      @urlpath_cache_size = urlpath_cache_size
      @urlpath_lru_cache  = urlpath_cache_size > 0 ? {} : nil
      #; [!wsz8g] compiles urlpath mapping passed.
      @fixed_endpoints    = {}  # urlpath patterns which have no urlpath params
      @variable_endpoints = []  # urlpath patterns which have any ulrpath param
      @all_endpoints      = []  # all urlpath patterns (fixed + variable)
      @urlpath_rexp       = build(urlpath_mapping)
    end

    private

    def build(urlpath_mapping)
      #; [!6f3vl] compiles urlpath mapping.
      empty_pargs = [].freeze
      rexp_str = traverse(urlpath_mapping, "") do |full_urlpath, action_class, action_methods|
        #; [!z2iax] classifies urlpath contains any parameter as variable one.
        if has_urlpath_param?(full_urlpath)
          pattern, pnames, procs = compile_urlpath(full_urlpath, true)
          rexp  = Regexp.compile("\\A#{pattern}\\z")
          range = @enable_urlpath_param_range ? range_of_urlpath_param(full_urlpath) : nil
          tuple = [full_urlpath, action_class, action_methods, rexp, pnames, procs, range]
          @variable_endpoints << tuple
        #; [!rvdes] classifies urlpath contains no parameters as fixed one.
        else
          tuple = [full_urlpath, action_class, action_methods, empty_pargs]
          @fixed_endpoints[full_urlpath] = tuple
        end
        #
        @all_endpoints << tuple
      end
      return Regexp.compile("\\A#{rexp_str}\\z")
    end

    def traverse(urlpath_mapping, base_urlpath="", &block)
      buf = []
      urlpath_mapping.each do |urlpath, target|
        curr_urlpath = "#{base_urlpath}#{urlpath}"
        rexp_str = nil
        #; [!w45ad] can compile nested array.
        if target.is_a?(Array)
          rexp_str = traverse(target, curr_urlpath, &block)
        #; [!wd2eb] accepts subclass of Action class.
        else
          #; [!l2kz5] requires library when filepath and classname specified.
          klass = target.is_a?(String) ? require_action_class(target) : target
          #; [!irt5g] raises TypeError when unknown object specified.
          klass.is_a?(Class) && klass < BaseAction  or
            raise TypeError.new("Action class or nested array expected, but got #{klass.inspect}")
          #; [!6xwhq] builds action infos for each action methods.
          action_class = klass
          action_class._build_action_info(curr_urlpath)
          #
          buf2 = []
          action_class._mappings.each do |upath, action_methods|
            validate(action_class, action_methods)
            full_urlpath = "#{curr_urlpath}#{upath}"
            if has_urlpath_param?(full_urlpath)
              buf2 << "#{compile_urlpath(upath)[0]}(\\z)"  # ex: /{id} -> /\d+(\z)
            end
            yield full_urlpath, action_class, action_methods
          end
          rexp_str = build_rexp_str(buf2)
        end
        #; [!bcgc9] skips classes which have only fixed urlpaths.
        buf << "#{compile_urlpath(urlpath)[0]}#{rexp_str}" if rexp_str
      end
      #
      return build_rexp_str(buf)
    end

    ## ex: '/books', ['/\d+', '/\d+/edit']  ->  '/books(?:/\d+|/\d+/edit)'
    def build_rexp_str(buf)
      #; [!169ad] removes unnecessary grouping.
      n = buf.length
      return n == 0 ? nil : n == 1 ? buf[0] : "(?:#{buf.join('|')})"
    ensure
      buf.clear()   # for GC
    end

    #; [!92jcn] '{' and '}' are available in urlpath param pattern.
    URLPATH_PARAM_REXP = /\{(\w*)(?::(\w*)(?:<(.*?)>)?)?\}/

    ## ex: '/books/{id}', true  ->  ['/books/(\d+)', [['id', 'int', proc{|x| x.to_i}]]]
    def compile_urlpath(urlpath_pat, enable_capture=false)
      #; [!iln54] param names and conveter procs are nil when no urlpath params.
      pnames = nil   # urlpath parameter names  (ex: ['id'])
      procs  = nil   # proc objects to convert parameter value (ex: [proc{|x| x.to_i}])
      #
      rexp_str = urlpath_pat.gsub(URLPATH_PARAM_REXP) {
        #; [!9ofdd] supports urlpath param type, for example '{id:int}'.
        pname, ptype, pat  = $1, $2, $3
        ptype, pat, proc_ = resolve_param_type(pname, ptype, pat, urlpath_pat)
        #; [!lhtiz] skips empty param name.
        #; [!66zas] skips param name starting with '_'.
        skip = pname.empty? || pname.start_with?('_')
        pnames ||= []; pnames << pname unless skip
        procs  ||= []; procs  << proc_ unless skip
        #; [!bi7gr] captures urlpath params when 2nd argument is truthy.
        #; [!mprbx] ex: '/{id:x|y}' -> '/(x|y)', '/{:x|y}' -> '/(?:x|y)'
        if enable_capture && ! skip
          pat = "(#{pat})"
        elsif pat =~ /\|/
          pat = "(?:#{pat})"
        end
        pat
      }
      #; [!awfgs] returns regexp string, param names, and converter procs.
      return rexp_str, pnames, procs   # ex: '/books/(\d+)', ['id'], [proc{|x| x.to_i}]}]
    end

    def has_urlpath_param?(urlpath)
      return urlpath.include?('{')
    end

    _to_date = proc {|s|
      begin
        yr, mo, dy = s.split('-')
        Date.new(yr.to_i, mo.to_i, dy.to_i)
      rescue
        raise HttpException.new(404)
      end
    }
    URLPATH_PARAM_TYPES = [
      # ptype , pname regexp    , urlpath pattern      , converter
      ['int'  , /(?:^|_)id\z/   , '\d+'                , proc {|s| s.to_i }],
      ['date' , /(?:^|_)date\z/ , '\d\d\d\d-\d\d-\d\d' , _to_date          ],
      ['str'  , nil             , '[^/]+'              , nil               ],
    ]
    _to_date = nil

    def resolve_param_type(pname, ptype, pattern, urlpath)
      tuple = nil
      if ! ptype || ptype.empty?
        tuple = URLPATH_PARAM_TYPES.find {|t| pname =~ t[1] }
        ptype = tuple ? tuple[0] : 'str'
      end
      tuple ||= URLPATH_PARAM_TYPES.find {|t| t[0] == ptype }  or
        raise ActionMappingError.new("'#{urlpath}': unknown param type '#{ptype}'.")
      pattern   = tuple[2] if ! pattern || pattern.empty?
      converter = tuple[3]   # ex: '123' -> 123, '2000-01-01' -> Date.new(2000, 1, 1)
      return ptype, pattern, converter
    end

    ## range object to retrieve urlpath parameter value faster than Regexp matching
    ## ex:
    ##   urlpath_pat == '/books/{id}/edit'
    ##   range = _range_of_urlpath_param(urlpath_pat)
    ##   p range                       #=> 7..-6 (Range object)
    ##   p "/books/123/edit"[range]    #=> '123'
    def range_of_urlpath_param(urlpath)
      i = 0
      m = nil
      urlpath.scan(URLPATH_PARAM_REXP) do
        i += 1
        m = Regexp.last_match
      end
      return nil unless i == 1
      return m.begin(0) .. (m.end(0) - urlpath.length - 1)  # ex: 7..-6 (Range object)
    end

    ## ex: './api/admin/books:Admin::BookAPI'  ->  Admin::BookAPI
    def require_action_class(filepath_and_classname)
      #; [!px9jy] requires file and finds class object.
      str = filepath_and_classname   # ex: './admin/api/book:Admin::BookAPI'
      filepath, classname = filepath_and_classname.split(':', 2)
      begin
        require filepath
      rescue LoadError => ex
        #; [!dlcks] don't rescue LoadError when it is not related to argument.
        raise unless ex.path == filepath
        #; [!mngjz] raises error when failed to load file.
        raise LoadError.new("'#{str}': cannot load '#{filepath}'.")
      end
      #; [!8n6pf] class name may have module prefix name.
      #; [!6lv7l] raises error when action class not found.
      begin
        klass = classname.split('::').inject(Object) {|cls, x| cls.const_get(x) }
      rescue NameError
        raise NameError.new("'#{str}': class not found (#{classname}).")
      end
      #; [!thf7t] raises TypeError when not a class.
      klass.is_a?(Class)  or
        raise TypeError.new("'#{str}': class name expected but got #{klass.inspect}.")
      #; [!yqcgx] raises TypeError when not a subclass of K8::Action.
      klass < Action  or
        raise TypeError.new("'#{str}': expected subclass of K8::Action but not.")
      #
      return klass
    end

    ## raises error when action method is not defined in action class
    def validate(action_class, action_methods)
      #; [!ue766] raises error when action method is not defined in action class.
      action_methods.each do |req_meth, action_name|
        action_class.method_defined?(action_name)  or
          raise UnknownActionMethodError.new("#{req_meth.inspect}=>#{action_name.inspect}: unknown action method in #{action_class}.")
      end
    end

    public

    def find(req_urlpath)
      #; [!j34yh] finds from fixed urlpaths at first.
      tuple = @fixed_endpoints[req_urlpath]
      return tuple[1..-1] if tuple     # ex: [BooksAction, {:GET=>:do_index}, []]
      #; [!uqwr7] uses LRU as cache algorithm.
      cache = @urlpath_lru_cache
      if cache && (result = cache.delete(req_urlpath))
        cache[req_urlpath] = result    # delete & append to simulate LRU
        return result
      end
      #; [!sos5i] returns nil when request path not matched to urlpath patterns.
      m = @urlpath_rexp.match(req_urlpath)
      return nil unless m
      #; [!95q61] finds from variable urlpath patterns when not found in fixed ones.
      index = m.captures.find_index('')
      tuple = @variable_endpoints[index]
      _, action_class, action_methods, urlpath_rexp, pnames, procs, range = tuple
      #; [!1k1k5] converts urlpath param values by converter procs.
      if range
        str = req_urlpath[range]
        pvalues = [procs[0] ? procs[0].call(str) : str]
      else
        strs = urlpath_rexp.match(req_urlpath).captures
        pvalues = \
          case procs.length
          when 1; [procs[0] ? procs[0].call(strs[0]) : strs[0]]
          when 2; [procs[0] ? procs[0].call(strs[0]) : strs[0],
                   procs[1] ? procs[1].call(strs[1]) : strs[1]]
          when 3; [procs[0] ? procs[0].call(strs[0]) : strs[0],
                   procs[1] ? procs[1].call(strs[1]) : strs[1],
                   procs[2] ? procs[2].call(strs[2]) : strs[2]]
          else  ; procs.zip(strs).map {|pr, v| pr ? pr.call(v) : v }
          end    # ex: ["123"] -> [123]
      end
      #; [!jyxlm] returns action class, action methods and urlpath param args.
      result = [action_class, action_methods, pvalues]
      #; [!uqwr7] stores result into cache if cache is enabled.
      if cache
        cache[req_urlpath] = result
        #; [!3ps5g] deletes item from cache when cache size over limit.
        cache.shift() if cache.length > @urlpath_cache_size
      end
      #
      return result
    end

    def each
      #; [!2gwru] returns Enumerator if block is not provided.
      return to_enum(:each) unless block_given?
      #; [!7ynne] yields each urlpath pattern, action class and action methods.
      @all_endpoints.each do |tuple|
        urlpath_pat, action_class, action_methods, _ = tuple
        yield urlpath_pat, action_class, action_methods
      end
      self
    end

  end


  class RackRequest

    def initialize(env)
      #; [!yb9k9] sets @env.
      @env = env
      #; [!yo22o] sets @meth as Symbol value.
      @meth = HTTP_REQUEST_METHODS[env['REQUEST_METHOD']]  or
        raise HTTPException.new(400, "#{env['REQUEST_METHOD'].inspect}: unknown request method.")
      #; [!twgmi] sets @path.
      @path = (x = env['PATH_INFO'])
      #; [!ae8ws] uses SCRIPT_NAME as urlpath when PATH_INFO is not provided.
      @path = env['SCRIPT_NAME'] if x.nil? || x.empty?
    end

    attr_reader :env, :meth, :path

    ## (experimental; use #meth instead)
    def method(name=nil)    # :nodoc:
      #; [!084jo] returns current request method when argument is not specified.
      #; [!gwskf] calls Object#method() when argument specified.
      return name ? super : @meth
    end

    def header(name)
      #; [!1z7wj] returns http header value from environment.
      return @env["HTTP_#{name.upcase.sub('-', '_')}"]
    end

    def request_method
      #; [!y8eos] returns env['REQUEST_METHOD'] as string.
      return @env['REQUEST_METHOD']
    end

    ##--
    #def get?         ; @meth == :GET           ; end
    #def post?        ; @meth == :POST          ; end
    #def put?         ; @meth == :PUT           ; end
    #def delete?      ; @meth == :DELETE        ; end
    #def head?        ; @meth == :HEAD          ; end
    #def patch?       ; @meth == :PATCH         ; end
    #def options?     ; @meth == :OPTIONS       ; end
    #def trace?       ; @meth == :TRACE         ; end
    ##++

    def script_name  ; @env['SCRIPT_NAME' ] || ''; end   # may be empty
    def path_info    ; @env['PATH_INFO'   ] || ''; end   # may be empty
    def query_string ; @env['QUERY_STRING'] || ''; end   # may be empty
    def server_name  ; @env['SERVER_NAME' ]      ; end   # should NOT be empty
    def server_port  ; @env['SERVER_PORT' ].to_i ; end   # should NOT be empty

    def content_type
      #; [!95g9o] returns env['CONTENT_TYPE'].
      return @env['CONTENT_TYPE']
    end

    def content_length
      #; [!0wbek] returns env['CONTENT_LENGHT'] as integer.
      len = @env['CONTENT_LENGTH']
      return len ? len.to_i : len
    end

    def referer          ; @env['HTTP_REFERER']         ; end
    def user_agent       ; @env['HTTP_USER_AGENT']      ; end
    def x_requested_with ; @env['HTTP_X_REQUESTED_WITH']; end

    def xhr?
      #; [!hsgkg] returns true when 'X-Requested-With' header is 'XMLHttpRequest'.
      return self.x_requested_with == 'XMLHttpRequest'
    end

    def client_ip_addr
      #; [!e1uvg] returns 'X-Real-IP' header value if provided.
      addr = @env['HTTP_X_REAL_IP']          # nginx
      return addr if addr
      #; [!qdlyl] returns first item of 'X-Forwarded-For' header if provided.
      addr = @env['HTTP_X_FORWARDED_FOR']    # apache, squid, etc
      return addr.split(',').first if addr
      #; [!8nzjh] returns 'REMOTE_ADDR' if neighter 'X-Real-IP' nor 'X-Forwarded-For' provided.
      addr = @env['REMOTE_ADDR']             # http standard
      return addr
    end

    def scheme
      #; [!jytwy] returns 'https' when env['HTTPS'] is 'on'.
      return 'https' if @env['HTTPS'] == 'on'
      #; [!zg8r2] returns env['rack.url_scheme'] ('http' or 'https').
      return @env['rack.url_scheme']
    end

    def rack_version      ; @env['rack.version']      ; end  # ex: [1, 3]
    def rack_url_scheme   ; @env['rack.url_scheme']   ; end  # ex: 'http' or 'https'
    def rack_input        ; @env['rack.input']        ; end  # ex: $stdout
    def rack_errors       ; @env['rack.errors']       ; end  # ex: $stderr
    def rack_multithread  ; @env['rack.multithread']  ; end  # ex: true
    def rack_multiprocess ; @env['rack.multiprocess'] ; end  # ex: true
    def rack_run_once     ; @env['rack.run_once']     ; end  # ex: false
    def rack_session      ; @env['rack.session']      ; end  # ex: {}
    def rack_logger       ; @env['rack.logger']       ; end  # ex: Logger.new
    def rack_hijack       ; @env['rack.hijack']       ; end  # ex: callable object
    def rack_hijack?      ; @env['rack.hijack?']      ; end  # ex: true or false
    def rack_hijack_io    ; @env['rack.hijack_io']    ; end  # ex: socket object

    def params_query
      #; [!6ezqw] parses QUERY_STRING and returns it as Hash/dict object.
      #; [!o0ws7] unquotes both keys and values.
      return @params_query ||= Util.parse_query_string(@env['QUERY_STRING'] || "")
    end
    alias query params_query

    MAX_POST_SIZE      =  10*1024*1024
    MAX_MULTIPART_SIZE = 100*1024*1024

    def params_form
      d = @params_form
      return d if d
      #
      d = @params_form = _parse_post_data(:form)
      return d
    end
    alias form params_form

    def params_multipart
      d1 = @params_form
      d2 = @params_file
      return d1, d2 if d1 && d2
      d1, d2 = _parse_post_data(:multipart)
      @params_form = d1; @params_file = d2
      return d1, d2
    end
    alias multipart params_multipart

    def params_json
      d = @params_json
      return d if d
      d = @params_json = _parse_post_data(:json)
      return d
    end
    alias json params_json

    def _parse_post_data(kind)
      #; [!q88w9] raises error when content length is missing.
      cont_len = @env['CONTENT_LENGTH']  or
        raise HttpException.new(400, 'Content-Length header expected.')
      #; [!gi4qq] raises error when content length is invalid.
      cont_len =~ /\A\d+\z/  or
        raise HttpException.new(400, 'Content-Length should be an integer.')
      #
      len = cont_len.to_i
      case @env['CONTENT_TYPE']
      #; [!59ad2] parses form parameters and returns it as Hash object when form requested.
      when 'application/x-www-form-urlencoded'
        kind == :form  or
          raise HttpException.new(400, 'unexpected form data (expected multipart).')
        #; [!puxlr] raises 400 error when content length is too large (> 10MB).
        len <= MAX_POST_SIZE  or
          raise HttpException.new(400, 'Content-Length is too large.')
        qstr = @env['rack.input'].read(len)
        d = Util.parse_query_string(qstr)
        return d
      #; [!y1jng] parses multipart when multipart form requested.
      when /\Amultipart\/form-data(?:;\s*boundary=(.*))?/
        kind == :multipart  or
          raise HttpException.new(400, 'unexpected multipart data.')
        boundary = $1  or
          raise HttpException.new(400, 'bounday attribute of multipart required.')
        #; [!mtx6t] raises error when content length of multipart is too large (> 100MB).
        len <= MAX_MULTIPART_SIZE  or
          raise HttpException.new(400, 'Content-Length of multipart is too large.')
        d1, d2 = Util.parse_multipart(@env['rack.input'], boundary, len, nil, nil)
        return d1, d2
      #; [!ugik5] parses json data and returns it as hash object when json data is sent.
      when /\Aapplication\/json\b/
        kind == :json  or
          raise HttpException.new(400, 'unexpected JSON data.')
        json_str = @env['rack.input'].read(10*1024*1024)   # TODO
        d = JSON.parse(json_str)
      #; [!p9ybb] raises error when not a form data.
      else
        raise HttpException.new(400, 'POST data expected, but not.')
      end
    end
    private :_parse_post_data

    def params
      #; [!erlc7] parses QUERY_STRING when request method is GET or HEAD.
      #; [!cr0zj] parses JSON when content type is 'application/json'.
      #; [!j2lno] parses form parameters when content type is 'application/x-www-form-urlencoded'.
      #; [!4rmn9] parses multipart when content type is 'multipart/form-data'.
      if @meth == :GET || @meth == :HEAD
        return params_query()
      end
      case @env['CONTENT_TYPE']
      when /\Aapplication\/json\b/
        return params_json()
      when /\Aapplication\/x-www-form-urlencoded\b/
        return params_form()
      when /\Amultipart\/form-data\b/
        return params_multipart()
      else
        return {}
      end
    end

    def cookies
      #; [!c9pwr] parses cookie data and returns it as hash object.
      return @cookies ||= Util.parse_cookie_string(@env['HTTP_COOKIE'] || "")
    end

    def clear
      #; [!0jdal] removes uploaded files.
      d = nil
      d.each {|_, uploaded| uploaded.clean() } if (d = @params_file)
    end

  end


  class RackResponse

    def initialize
      @status_code = 200
      @headers = {}
    end

    attr_accessor :status_code
    attr_reader :headers
    ## for compatibility with Rack::Response
    alias status status_code
    alias status= status_code=

    def content_type
      return @headers['Content-Type']
    end

    def content_type=(content_type)
      @headers['Content-Type'] = content_type
    end

    def content_length
      s = @headers['Content-Length']
      return s ? s.to_i : nil
    end

    def content_length=(length)
      @headers['Content-Length'] = length.to_s
    end

    def set_cookie(name, value, domain: nil, path: nil, expires: nil, max_age: nil, httponly: nil, secure: nil)
      s = "#{name}=#{value}"
      s << "; Domain=#{domain}"   if domain
      s << "; Path=#{path}"       if path
      s << "; Expires=#{expires}" if expires
      s << "; Max-Age=#{max_age}" if max_age
      s << "; HttpOnly"           if httponly
      s << "; Secure"             if secure
      value = @headers['Set-Cookie']
      @headers['Set-Cookie'] = value ? (value << "\n" << s) : s
      return value
    end

    def clear
    end

  end


  REQUEST_CLASS  = RackRequest
  RESPONSE_CLASS = RackResponse

  def self.REQUEST_CLASS=(klass)
    #; [!7uqb4] changes default request class.
    remove_const :REQUEST_CLASS
    const_set :REQUEST_CLASS, klass
  end

  def self.RESPONSE_CLASS=(klass)
    #; [!c1bd0] changes default response class.
    remove_const :RESPONSE_CLASS
    const_set :RESPONSE_CLASS, klass
  end


  class RackApplication

    def initialize(urlpath_mapping=[], urlpath_cache_size: 0,
                                       enable_urlpath_param_range: true)
      #; [!vkp65] mounts urlpath mappings.
      @mapping = ActionMapping.new(urlpath_mapping,
                                   urlpath_cache_size: urlpath_cache_size,
                                   enable_urlpath_param_range: enable_urlpath_param_range)
    end

    def find(req_path)
      #; [!o0rnr] returns action class, action methods, urlpath names and values.
      return @mapping.find(req_path)
    end

    def lookup(req_meth, req_path, query_string="")
      #; [!7476i] uses '_method' value of query string as request method when 'POST' method.
      if req_meth == :POST && query_string =~ /\A_method=(\w+)/
        req_meth = HTTP_REQUEST_METHODS[$1.upcase] || $1.upcase
      end
      #
      tuple = find(req_path)
      unless tuple
        #; [!c0job] redirects only when request method is GET or HEAD.
        if req_meth == :GET || req_meth == :HEAD
          #; [!u1qfv] raises 301 when urlpath not found but found with tailing '/'.
          #; [!kbff3] raises 301 when urlpath not found but found without tailing '/'.
          rpath  = req_path
          rpath2 = rpath.end_with?('/') ? rpath[0..-2] : rpath + '/'
          if find(rpath2)
            #; [!cgxx4] adds query string to 'Location' header when redirecting.
            qs = query_string
            location = ! qs || qs.empty? ? rpath2 : "#{rpath2}?#{qs}"
            status = 301              # 301 Moved Permanently
            raise HttpException.new(status, nil, {'Location'=>location})
          end
        end
        #; [!hdy1f] raises HTTP 404 when urlpath not found.
        raise HttpException.new(404)  # 404 Not Found
      end
      action_class, action_methods, urlpath_args = tuple
      #; [!0znwr] uses 'GET' method to find action when request method is 'HEAD'.
      d = action_methods
      action_name = d[req_meth] || (req_meth == :HEAD ? d[:GET] : nil) || d[:ANY]
      #; [!bfpav] raises HTTP 405 when urlpath found but request method not allowed.
      action_name  or
        raise HttpException.new(405)  # 405 Method Not Allowed
      return action_class, action_name, urlpath_args
    end

    def call(env)
      #; [!uvmxe] takes env object.
      #; [!gpe4g] returns status, headers and content.
      #; [!eb2ms] returns 301 when urlpath not found but found with tailing '/'.
      #; [!02dow] returns 301 when urlpath not found but found without tailing '/'.
      #; [!2a9c9] adds query string to 'Location' header.
      #; [!vz07j] redirects only when request method is GET or HEAD.
      #; [!l6kmc] uses 'GET' method to find action when request method is 'HEAD'.
      #; [!4vmd3] uses '_method' value of query string as request method when 'POST' method.
      #; [!rz13i] returns HTTP 404 when urlpath not found.
      #; [!rv3cf] returns HTTP 405 when urlpath found but request method not allowed.
      req  = REQUEST_CLASS.new(env)
      resp = RESPONSE_CLASS.new
      begin
        ret = handle_request(req, resp)
      rescue HttpException => ex
        ret = handle_http(ex, req, resp)
      rescue Exception => ex
        ret = handle_error(ex, req, resp)
      ensure
        #; [!vdllr] clears request and response if possible.
        req.clear()  if req.respond_to?(:clear)
        resp.clear() if resp.respond_to?(:clear)
      end
      return ret
    end

    protected

    def handle_request(req, resp)
      #; [!0fgbd] finds action class and invokes action method with urlpath params.
      req_meth = HTTP_REQUEST_METHODS[req.env['REQUEST_METHOD']] || req.env['REQUEST_METHOD']
      tuple = lookup(req_meth, req.path, req.env['QUERY_STRING'])
      action_class, action_name, pargs = tuple  # ex: [BooksAction, :do_show, [123]]
      action_obj = action_class.new(req, resp)
      content = action_obj.handle_action(action_name, pargs)
      #; [!9wp9z] returns empty body when request method is HEAD.
      content = [""] if req_meth == :HEAD
      return [resp.status, resp.headers, content]
    end

    def handle_http(ex, req, resp)
      if json_expected?(req)
        content = render_http_exception_as_json(ex, req, resp)
        content_type = "application/json"
      else
        content = render_http_exception_as_html(ex, req, resp)
        content_type = "text/html;charset=utf-8"
      end
      headers = {
        "Content-Type"   => content_type,
        "Content-Length" => content.bytesize.to_s,
      }
      headers.update(ex.response_headers) if ex.response_headers
      return [ex.status_code, headers, [content]]
    end

    def handle_error(ex, req, resp)
      raise ex
    end

    def render_http_exception_as_json(ex, req, resp)
      return JSON.dump({
        "error"  => ex.message,
        "status" => "#{ex.status_code} #{ex.status_message}",
      })
    end

    def render_http_exception_as_html(ex, req, resp)
      return <<"END"
<div>
<h2>#{ex.status_code} #{ex.status_message}</h2>
<p>#{ex.message}</p>
</div>
END
    end

    def json_expected?(req)
      return true if req.path.end_with?('.json')
      return true if req.env['HTTP_X_REQUESTED_WITH'] == 'XMLHttpRequest'
      return false
    end

    def lookup_autoredirect_location(req)
      location = req.path.end_with?('/') ? req.path[0..-2] : "#{req.path}/"
      return nil unless find(location)
      #; [!2a9c9] adds query string to 'Location' header.
      qs = req.env['QUERY_STRING']
      return qs && ! qs.empty? ? "#{location}?#{qs}" : location
    end

    public

    def each_mapping(&block)
      #; [!cgjyv] yields full urlpath pattern, action class and action methods.
      @mapping.each(&block)
      self
    end

    def show_mappings()
      #; [!u1g77] returns all mappings as YAML string.
      req_methods = HTTP_REQUEST_METHODS.values() + [:ANY]
      s = ""
      each_mapping do |full_urlpath_pat, action_class, action_methods|
        arr = req_methods.collect {|req_meth|
          action_name = action_methods[req_meth]
          action_name ? "#{req_meth}: #{action_name}" : nil
        }.compact()
        s << "- urlpath: #{full_urlpath_pat}\n"
        s << "  class:   #{action_class}\n"
        s << "  methods: {#{arr.join(', ')}}\n"
        s << "\n"
      end
      return s
    end

  end


  class SecretValue < Object

    def initialize(name=nil)
      #; [!fbwnh] takes environment variable name.
      @name = name
    end

    attr_reader :name

    def value
      #; [!gg06v] returns environment variable value.
      return @name ? ENV[@name] : nil
    end

    def to_s
      #; [!7ymqq] returns '<SECRET>' string when name not eixst.
      #; [!x6edf] returns 'ENV[<name>]' string when name exists.
      return @name ? "ENV['#{@name}']" : "<SECRET>"
    end

    #; [!j27ji] 'inspect()' is alias of 'to_s()'.
    alias inspect to_s

    def [](name)
      #; [!jjqmn] creates new instance object with name.
      self.class.new(name)
    end

  end


  class BaseConfig < Object

    SECRET = SecretValue.new

    def initialize(freeze: true)
      #; [!vvd1n] copies key and values from class object.
      self.class.each do |key, val, _, _|
        #; [!xok12] when value is SECRET...
        if val.is_a?(SecretValue)
          #; [!a4a4p] raises error when key not specified.
          val.name  or
            raise ConfigError.new("config '#{key}' should be set, but not.")
          #; [!w4yl7] raises error when ENV value not specified.
          ENV[val.name]  or
            raise ConfigError.new("config '#{key}' depends on ENV['#{val.name}'], but not set.")
          #; [!he20d] get value from ENV.
          val = ENV[val.name]
        end
        instance_variable_set("@#{key}", val)
      end
      #; [!6dilv] freezes self and class object if 'freeze:' is true.
      self.class.freeze if freeze
      self.freeze       if freeze
    end

    def self.validate_values   # :nodoc:
      not_set = []
      not_env = []
      each() do |key, val, _, _|
        if val.is_a?(SecretValue)
          if ! val.name
            not_set << [key, val]
          elsif ! ENV[val.name]
            not_env << [key, val]
          end
        end
      end
      return nil if not_set.empty? && not_env.empty?
      sb = []
      sb << "**"
      sb << "** ERROR: insufficient config"
      unless not_set.empty?
        sb << "**"
        sb << "** The following configs should be set, but not."
        sb << "**"
        not_set.each do |key, val|
          sb <<  "**   %-25s %s" % [key, val]
        end
      end
      unless not_env.empty?
        sb << "**"
        sb << "** The following configs expect environment variable, but not set."
        sb << "**"
        not_env.each do |key, val|
          sb <<  "**   %-25s %s" % [key, val]
        end
      end
      sb << "**"
      sb << ""
      return sb.join("\n")
    end

    private

    def self.__all
      return @__all ||= {}
    end

    public

    def self.has?(key)
      #; [!dv87n] returns true iff key is set.
      return __all().key?(key)
    end

    def self.put(key, value, desc=nil)
      #; [!h9b47] defines getter method.
      attr_reader key
      d = __all()
      #; [!mun1v] keeps secret flag.
      if d[key]
        desc ||= d[key][1]
        secret = d[key][2]
      else
        secret = value == SECRET
      end
      #; [!ncwzt] stores key with value, description and secret flag.
      d[key] = [value, desc, secret]
      nil
    end

    def self.add(key, value, desc=nil)
      #; [!envke] raises error when already added.
      ! self.has?(key)  or
        raise K8::ConfigError.new("add(#{key.inspect}, #{value.inspect}): cannot add because already added; use set() or put() instead.")
      #; [!6cmb4] adds new key, value and desc.
      self.put(key, value, desc)
    end

    def self.set(key, value, desc=nil)
      #; [!2yis0] raises error when not added yet.
      self.has?(key)  or
        raise K8::ConfigError.new("set(#{key.inspect}, #{value.inspect}): cannot set because not added yet; use add() or put() instead.")
      #; [!3060g] sets key, value and desc.
      self.put(key, value, desc)
    end

    def self.each
      #; [!iu88i] yields with key, value, desc and secret flag.
      __all().each do |key, (value, desc, secret)|
        yield key, value, desc, secret
      end
      nil
    end

    def self.get(key, default=nil)
      #; [!zlhnp] returns value corresponding to key.
      #; [!o0k05] returns default value (=nil) when key is not added.
      tuple = __all()[key]
      return tuple ? tuple.first : default
    end

    def [](key)
      #; [!jn9l5] returns value corresponding to key.
      return __send__(key)
    end

    def get_all(prefix_key)
      #; [!4ik3c] returns all keys and values which keys start with prefix as hash object.
      prefix = "@#{prefix_key}"
      symbol_p = prefix_key.is_a?(Symbol)
      range = prefix.length..-1
      d = {}
      self.instance_variables.each do |ivar|
        if ivar.to_s.start_with?(prefix)
          val = self.instance_variable_get(ivar)
          key = ivar[range].intern
          key = key.intern if symbol_p
          d[key] = val
        end
      end
      return d
    end

  end


  class ConfigError < StandardError
  end


end
