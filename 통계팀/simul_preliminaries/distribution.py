#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
cdf_calculator.py
-----------------
이 파일은, 좌측 및 우측 구간의 균등분포를 기반으로 5가지 케이스(4/0, 3/1, 2/2, 1/3, 0/4)에 대한
piecewise PDF를 계산한 후, 전체 조합에 따른 최종 PDF(final_pdf)를 구성합니다.
그리고 두 숫자 a, b를 입력받아 구간 [a, b] 사이의 누적 확률(CDF 차이)을 계산하는
함수 probability_interval(a, b)를 제공합니다.

사용 예:
    $ python cdf_calculator.py -1 1
    구간 [-1.0, 1.0]의 확률: <계산된 확률>

교수님의 지시대로 모든 기능을 하나의 파일로 통합하였습니다.
"""

import sys
import itertools
from math import comb

# =========================
# 1. 다항식 관련 함수들
# =========================
def eval_poly(poly, x):
    """다항식 poly (계수 리스트)를 x에서 평가 (poly = [a0, a1, ...]는 a0 + a1*x + ...)"""
    return sum(c * (x ** i) for i, c in enumerate(poly))

def poly_integral(poly):
    """다항식 poly의 부정적분(적분 상수 0) 반환.
       예: [a0, a1, a2, ...] -> [0, a0, a1/2, a2/3, ...]"""
    return [0] + [poly[i] / (i + 1) for i in range(len(poly))]

def eval_integral_poly(poly, x):
    """다항식 poly의 부정적분을 x에서 평가"""
    integ = poly_integral(poly)
    return eval_poly(integ, x)

def poly_add(poly1, poly2):
    """두 다항식의 덧셈 (poly1 + poly2)"""
    n = max(len(poly1), len(poly2))
    res = [0] * n
    for i in range(n):
        a = poly1[i] if i < len(poly1) else 0
        b = poly2[i] if i < len(poly2) else 0
        res[i] = a + b
    return res

def poly_scale(poly, scalar):
    """다항식 poly의 모든 계수를 scalar배 함"""
    return [scalar * c for c in poly]

def poly_subtract(poly1, poly2):
    """두 다항식의 뺄셈 (poly1 - poly2)"""
    return poly_add(poly1, poly_scale(poly2, -1))

def poly_mul(poly1, poly2):
    """두 다항식의 곱 (합성곱)"""
    res = [0] * (len(poly1) + len(poly2) - 1)
    for i, a in enumerate(poly1):
        for j, b in enumerate(poly2):
            res[i+j] += a * b
    return res

def poly_compose(poly, shift):
    """
    다항식 poly(x)를 x -> (z - shift)로 치환하여 Q(z)=poly(z-shift)를 구함.
    poly: 계수 리스트 [a0, a1, ...]
    반환: Q(z)를 나타내는 계수 리스트.
    """
    n = len(poly)
    result = [0] * n
    for i, a in enumerate(poly):
        for j in range(i+1):
            result[j] += a * comb(i, j) * ((-shift)**(i-j))
    return result

# =========================
# 2. Segment 클래스 및 구간 생성
# =========================
class Segment:
    def __init__(self, start, end, poly):
        self.start = start      # 구간 시작
        self.end = end          # 구간 끝
        self.poly = poly        # 해당 구간에서의 PDF를 나타내는 다항식 (리스트)

    def __repr__(self):
        return f"Segment([{self.start}, {self.end}], poly={self.poly})"

# 좌측 구간: -3 ~ 0, 8개 구간
left_intervals = []
delta_left = 3 / 8
for i in range(8):
    a = -3 + i * delta_left
    b = -3 + (i+1) * delta_left
    # 균등분포 PDF: 1/(구간 길이) * (선택확률 1/15)
    c = 1 / (15 * delta_left)
    left_intervals.append(Segment(a, b, [c]))

# 우측 구간: 0 ~ 3, 7개 구간
right_intervals = []
delta_right = 3 / 7
for i in range(7):
    a = 0 + i * delta_right
    b = 0 + (i+1) * delta_right
    c = 1 / (15 * delta_right)
    right_intervals.append(Segment(a, b, [c]))

# =========================
# 3. 합성곱(convolution) 관련 함수
# =========================
def convolve_two_uniform(seg1, seg2):
    """
    두 uniform 구간 seg1과 seg2의 합성곱.
    seg1: [a1, b1] 구간, 상수 pdf c1 (poly = [c1])
    seg2: [a2, b2] 구간, 상수 pdf c2 (poly = [c2])
    반환: 합성곱 결과로 얻은 piecewise linear 함수의 Segment 리스트.
    """
    a1, b1, c1 = seg1.start, seg1.end, seg1.poly[0]
    a2, b2, c2 = seg2.start, seg2.end, seg2.poly[0]
    segments = []
    z0 = a1 + a2
    z1 = a1 + b2
    z2 = b1 + a2
    z3 = b1 + b2
    # 첫 구간: 선형 증가
    poly1 = [-c1*c2*(a1+a2), c1*c2]
    segments.append(Segment(z0, z1, poly1))
    # 중간 구간: 상수
    if z1 < z2:
        segments.append(Segment(z1, z2, [c1*c2*(b2 - a2)]))
    # 마지막 구간: 선형 감소
    poly3 = [c1*c2*(b1+b2), -c1*c2]
    segments.append(Segment(z2, z3, poly3))
    return segments

def convolve_piecewise_with_uniform(piecewise_segments, uniform_seg):
    """
    piecewise_segments: 리스트, 각 원소는 Segment (정의역: [a, b], 다항식 poly)
    uniform_seg: 단일 uniform Segment (구간 [a2, b2], poly = [c2])
    반환: 두 함수의 합성곱 결과를 나타내는 새로운 Segment 리스트.
    (여기서는 seg.poly가 상수 또는 1차 함수인 경우에 한정)
    """
    new_segments = []
    c2 = uniform_seg.poly[0]
    a2, b2 = uniform_seg.start, uniform_seg.end
    for seg in piecewise_segments:
        a1, b1, poly1 = seg.start, seg.end, seg.poly
        F = poly_integral(poly1)
        # breakpoints 계산
        z_low = a1 + a2
        z_mid1 = b1 + a2
        z_mid2 = a1 + b2
        z_high = b1 + b2
        # Region 1: z in [z_low, z_mid1]
        F_comp1 = poly_compose(F, a2)
        F_a1 = eval_poly(F, a1)
        poly_region1 = poly_subtract(F_comp1, [F_a1])
        poly_region1 = poly_scale(poly_region1, c2)
        new_segments.append(Segment(z_low, z_mid1, poly_region1))
        # Region 2: z in [z_mid1, z_mid2] - 상수 값
        const_val = c2 * (eval_poly(F, b1) - eval_poly(F, a1))
        new_segments.append(Segment(z_mid1, z_mid2, [const_val]))
        # Region 3: z in [z_mid2, z_high]
        F_comp2 = poly_compose(F, b2)
        poly_region3 = poly_subtract([eval_poly(F, b1)], F_comp2)
        poly_region3 = poly_scale(poly_region3, c2)
        new_segments.append(Segment(z_mid2, z_high, poly_region3))
    return new_segments

def merge_piecewise_pdf(pw1, pw2):
    """
    두 piecewise PDF (Segment 리스트)를 병합합니다.
    각 Segment의 구간 경계점을 모두 모아 작은 구간으로 분할한 후,
    해당 구간에서 두 PDF의 다항식 값을 합산합니다.
    """
    boundaries = set()
    for seg in pw1 + pw2:
        boundaries.add(seg.start)
        boundaries.add(seg.end)
    boundaries = sorted(boundaries)
    merged = []
    for i in range(len(boundaries) - 1):
        a = boundaries[i]
        b = boundaries[i+1]
        poly_sum = [0]
        for seg in pw1:
            if seg.start <= a and seg.end >= b:
                poly_sum = poly_add(poly_sum, seg.poly)
        for seg in pw2:
            if seg.start <= a and seg.end >= b:
                poly_sum = poly_add(poly_sum, seg.poly)
        merged.append(Segment(a, b, poly_sum))
    return merged

def shift_piecewise_pdf(pw, shift):
    """
    piecewise PDF pw를 x -> x - shift 변환합니다.
    각 Segment의 구간은 [start+shift, end+shift]가 되고,
    다항식은 poly_compose를 이용해 변환합니다.
    """
    shifted = []
    for seg in pw:
        new_start = seg.start + shift
        new_end = seg.end + shift
        new_poly = poly_compose(seg.poly, shift)
        shifted.append(Segment(new_start, new_end, new_poly))
    return shifted

def convolve_segments_list(segments_list):
    """
    segments_list (Segment 리스트)에 대해 순차적으로 합성곱(convolution)을 수행합니다.
    초기 piecewise PDF는 segments_list[0]로 시작하여, 나머지 구간과 합성곱을 진행합니다.
    """
    piecewise = [segments_list[0]]
    for seg in segments_list[1:]:
        piecewise = convolve_piecewise_with_uniform(piecewise, seg)
        piecewise = merge_piecewise_pdf(piecewise, [])
    return piecewise

# =========================
# 4. 케이스별 및 전체 PDF 계산
# =========================
def compute_case_pdf(left_count, right_count):
    """
    좌측 구간(left_count개)과 우측 구간(right_count개)에서 4개를 선택한 조합에 대해
    합성곱한 PDF (piecewise)를 계산하고, 해당 케이스의 조합 수를 반환합니다.
    """
    case_pdf = None
    comb_count = 0
    for left_choice in itertools.combinations(left_intervals, left_count):
        for right_choice in itertools.combinations(right_intervals, right_count):
            comb_count += 1
            selected = list(left_choice) + list(right_choice)
            pdf_piece = convolve_segments_list(selected)
            if case_pdf is None:
                case_pdf = pdf_piece
            else:
                case_pdf = merge_piecewise_pdf(case_pdf, pdf_piece)
    return case_pdf, comb_count

def poly_scale_pdf(pw, scalar):
    """각 Segment의 다항식 계수에 scalar를 곱하여 스케일링합니다."""
    new_pw = []
    for seg in pw:
        new_pw.append(Segment(seg.start, seg.end, poly_scale(seg.poly, scalar)))
    return new_pw

def scale_pdf(piecewise, scale):
    """
    변수 변환 X -> X/scale에 따른 스케일 조정.
    Y = X/scale일 때, f_Y(y) = scale * f_X(scale * y)
    """
    scaled = []
    for seg in piecewise:
        new_start = seg.start / scale
        new_end = seg.end / scale
        new_poly = poly_scale(seg.poly, scale)
        scaled.append(Segment(new_start, new_end, new_poly))
    return scaled

def add_case_pdfs(case_results, total_comb):
    total_pdf = None
    for pdf_case, count_case in case_results:
        if total_pdf is None:
            total_pdf = poly_scale_pdf(pdf_case, count_case)
        else:
            total_pdf = merge_piecewise_pdf(total_pdf, poly_scale_pdf(pdf_case, count_case))
    return poly_scale_pdf(total_pdf, 1 / total_comb)

def compute_total_pdf():
    """
    5가지 케이스에 대해 PDF를 계산하여 전체 PDF(final_pdf)를 구성합니다.
    케이스: (4,0), (3,1), (2,2), (1,3), (0,4)
    """
    cases = [(4, 0), (3, 1), (2, 2), (1, 3), (0, 4)]
    case_results = []
    total_comb = 0
    for lc, rc in cases:
        pdf_case, count_case = compute_case_pdf(lc, rc)
        case_results.append((pdf_case, count_case))
        total_comb += count_case
    total_pdf = add_case_pdfs(case_results, total_comb)
    # 평균 계산: Y = X/4, f_Y(y) = 4 f_X(4y)
    final_pdf_local = scale_pdf(total_pdf, 4)
    return final_pdf_local

# 전역 변수 final_pdf: 전체 PDF (piecewise) 구성 결과
final_pdf = compute_total_pdf()

# =========================
# 5. CDF 및 구간 확률 함수
# =========================
def compute_cdf(x, piecewise_pdf):
    """
    주어진 piecewise_pdf에 대해, x까지의 누적 확률(CDF)을 계산합니다.
    """
    total = 0.0
    for seg in piecewise_pdf:
        if x >= seg.end:
            total += eval_integral_poly(seg.poly, seg.end) - eval_integral_poly(seg.poly, seg.start)
        elif x > seg.start:
            total += eval_integral_poly(seg.poly, x) - eval_integral_poly(seg.poly, seg.start)
    return total

def probability_between(a, b, piecewise_pdf):
    """구간 [a, b] 사이의 누적 확률을 계산합니다."""
    return compute_cdf(b, piecewise_pdf) - compute_cdf(a, piecewise_pdf)

def probability_interval(a, b):
    """
    두 숫자 a, b를 입력받아, 전역 변수 final_pdf를 이용하여
    구간 [a, b]의 누적 확률(CDF 차이)을 반환합니다.
    """
    return probability_between(a, b, final_pdf)

# =========================
# 6. 메인 실행: 커맨드라인 인자로 a, b를 받아 확률 계산
# =========================
if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python cdf_calculator.py <a> <b>")
        sys.exit(1)
    try:
        a_val = float(sys.argv[1])
        b_val = float(sys.argv[2])
    except ValueError:
        print("두 숫자를 올바르게 입력해 주십시오.")
        sys.exit(1)
    prob = probability_interval(a_val, b_val)
    print(f"구간 [{a_val}, {b_val}]의 확률: {prob}")
