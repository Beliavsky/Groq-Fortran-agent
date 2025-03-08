! Generated from prompt file: prompt_cauchy.txt
! Model used: qwen-2.5-coder-32b
! Time generated: 2025-03-08 10:28:41
! Generation time: 18.061 seconds
! Generated from prompt file: prompt_cauchy.txt
! Model used: qwen-2.5-coder-32b
! Time generated: 2025-03-08 10:28:23
! Generation time: 14.672 seconds
! Generated from prompt file: prompt_cauchy.txt
! Model used: qwen-2.5-coder-32b
! Time generated: 2025-03-08 10:28:08
! Generation time: 3.164 seconds
module constants
    implicit none
    integer, parameter :: dp = kind(1.0d0)
end module constants

module utilities
    use constants
    implicit none
contains
    function trimmed_mean(x, trim_prop) result(tm)
        real(kind=dp), intent(in) :: x(:)
        real(kind=dp), intent(in) :: trim_prop
        real(kind=dp) :: tm
        integer :: n, k
        real(kind=dp), allocatable :: x_sorted(:)
        
        n = size(x)
        k = int(trim_prop * n / 2.0_dp)
        if (2*k >= n) then
            tm = sum(x) / real(n, kind=dp)
        else
            allocate(x_sorted(n))
            x_sorted = x
            call sort(x_sorted)
            tm = sum(x_sorted(k+1:n-k)) / real(n - 2*k, kind=dp)
            deallocate(x_sorted)
        end if
    end function trimmed_mean
    
    subroutine sort(arr)
        real(kind=dp), intent(inout) :: arr(:)
        integer :: n, i, j
        real(kind=dp) :: temp
        
        n = size(arr)
        do i = 1, n-1
            do j = i+1, n
                if (arr(i) > arr(j)) then
                    temp = arr(i)
                    arr(i) = arr(j)
                    arr(j) = temp
                end if
            end do
        end do
    end subroutine sort
end module utilities

program cauchy_simulation
    use constants
    use utilities
    implicit none
    real(kind=dp), parameter :: pi = 4.0_dp * atan(1.0_dp)
    real(kind=dp), allocatable :: samples(:), trim_means(:,:)
    real(kind=dp) :: trim_proportions(6)
    integer :: i, j, n_samples, n_observations
    
    n_samples = 100
    n_observations = 1000
    trim_proportions = [0.0_dp, 0.1_dp, 0.2_dp, 0.3_dp, 0.4_dp, 0.45_dp]
    allocate(samples(n_observations), trim_means(n_samples, size(trim_proportions)))
    
    call random_seed()
    
    do i = 1, n_samples
        call random_number(samples)
        samples = tan(pi * (samples - 0.5_dp))
        do j = 1, size(trim_proportions)
            trim_means(i, j) = trimmed_mean(samples, trim_proportions(j))
        end do
    end do
    
    do j = 1, size(trim_proportions)
        print *, 'Trim proportion:', trim_proportions(j), 'Mean trimmed mean:', sum(trim_means(:,j)) / real(n_samples, kind=dp)
    end do
    
    deallocate(samples, trim_means)
end program cauchy_simulation