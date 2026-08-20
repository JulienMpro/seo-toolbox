from seotoolbox.logs import analyze_logs, parse_log


def test_parse_filter_and_analysis(tmp_path):
    path = tmp_path / "access.log"
    path.write_text('1.2.3.4 - - [20/Aug/2026:10:00:00 +0000] "GET /ok HTTP/1.1" 200 12 "-" "Googlebot/2.1"\n'
                    '1.2.3.5 - - [20/Aug/2026:10:01:00 +0000] "GET /missing HTTP/1.1" 404 0 "-" "Mozilla"\n')
    entries = parse_log(path)
    report = analyze_logs(entries)
    assert report.status_stats == {200: 1, 400: 1}
    assert report.bot_hits == [("20/Aug/2026", 1)]
    assert report.problem_urls == [(404, "/missing", 1)]
    assert len(parse_log(path, "googlebot")) == 1
