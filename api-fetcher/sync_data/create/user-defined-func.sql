-- 소숫점 5자리에서 올림(절상)하는 함수
CREATE OR REPLACE FUNCTION floor_5dp(numeric)
    RETURNS numeric AS
$$
BEGIN
    RETURN FLOOR($1 * 100000) / 100000;
END;
$$ LANGUAGE plpgsql IMMUTABLE
                    STRICT;