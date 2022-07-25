def get_ascii_bar(count, increment):
    # https://alexwlchan.net/2018/05/ascii-bar-charts/

    bar_chunks, remainder = divmod(int(count * 8 / increment), 8)

    bar = '█' * bar_chunks
    if remainder > 0:
        bar += chr(ord('█') + (8 - remainder))
    bar = bar or '▏'

    return bar
